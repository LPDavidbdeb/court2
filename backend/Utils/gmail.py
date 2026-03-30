import os.path
import json
from datetime import datetime, timedelta
from dateutil import parser
import locale
import base64
from email.header import decode_header, make_header

# IMPORTANT: Ensure you have these libraries installed in your environment:
# pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib python-dateutil

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


class GmailService:
    def __init__(self, client_secret_path, token_path="token.json"):
        self.client_secret_path = client_secret_path
        self.token_path = token_path
        self.service = None

    def connect(self):
        creds = None
        if os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            except json.JSONDecodeError:
                print(f"Warning: {self.token_path} is corrupted or empty. Re-authenticating.")
                creds = None
            except Exception as e:
                print(f"Error loading token from {self.token_path}: {e}. Re-authenticating.")
                creds = None

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("Credentials expired, attempting to refresh token...")
                try:
                    creds.refresh(Request())
                    print("Token refreshed successfully.")
                except Exception as e:
                    print(f"Failed to refresh token: {e}. Initiating new authorization flow...")
                    creds = None
            else:
                print("No valid credentials found or refresh failed. Initiating new authorization flow...")

            if not os.path.exists(self.client_secret_path):
                print(f"Error: Client secret file not found at {self.client_secret_path}")
                print("Please ensure the path is correct and the file exists.")
                return None

            try:
                flow = InstalledAppFlow.from_client_secrets_file(self.client_secret_path, SCOPES)
                creds = flow.run_local_server(port=0)
                print("Authentication successful via browser.")
            except Exception as e:
                print(f"Error during initial authentication flow: {e}")
                return None

            try:
                with open(self.token_path, "w") as token:
                    token.write(creds.to_json())
                print(f"New token saved to {self.token_path}.")
            except Exception as e:
                print(f"Error saving token to {self.token_path}: {e}")

        try:
            self.service = build("gmail", "v1", credentials=creds)
            print("Gmail API service object created.")
            return self.service
        except HttpError as error:
            print(f"An API error occurred while building the service: {error}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred while building the service: {e}")
            return None

    def _parse_date_to_gmail_format(self, date_string, lang='en'):
        """
        Parses a date string (English or French) into 'YYYY/MM/DD' format.
        """
        original_locale = locale.getlocale(locale.LC_TIME)
        try:
            if lang == 'fr':
                try:
                    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
                except locale.Error:
                    try:
                        locale.setlocale(locale.LC_TIME, 'fra')
                    except locale.Error:
                        locale.setlocale(locale.LC_TIME, '')
                        print(
                            "Warning: Could not set French locale. Date parsing might be less accurate for French dates.")
            elif lang == 'en':
                locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
            else:
                locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')

            parsed_date = parser.parse(date_string)
            return parsed_date.strftime('%Y/%m/%d')
        except ValueError:
            print(f"Error: Could not parse date string '{date_string}' with lang '{lang}'.")
            return None
        finally:
            locale.setlocale(locale.LC_TIME, original_locale)

    def _get_header_value(self, headers, name):
        """Helper to get a header value, handling potential encoding."""
        for header in headers:
            if header['name'].lower() == name.lower():
                return str(make_header(decode_header(header['value'])))
        return None

    def _get_message_body(self, payload):
        """
        Extracts and decodes the plain text or HTML body from a message payload.
        Prioritizes plain text.
        """
        if 'parts' in payload:
            for part in payload['parts']:
                mime_type = part.get('mimeType')
                if mime_type == 'text/plain' and 'body' in part and 'data' in part['body']:
                    return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                elif mime_type == 'text/html' and 'body' in part and 'data' in part['body']:
                    return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
            for part in payload['parts']:
                nested_body = self._get_message_body(part)
                if nested_body:
                    return nested_body
        elif 'body' in payload and 'data' in payload['body']:
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
        return None

    def _parse_message_data(self, message_raw):
        """
        Parses a raw Gmail API message dictionary into a structured dictionary.
        """
        message_id = message_raw['id']
        thread_id = message_raw['threadId']
        payload = message_raw['payload']
        headers = payload['headers']

        parsed_data = {
            'id': message_id,
            'threadId': thread_id,
            'snippet': message_raw.get('snippet'),
            'historyId': message_raw.get('historyId'),
            'internalDate': message_raw.get('internalDate'),
            'headers': {
                'Subject': self._get_header_value(headers, 'Subject'),
                'From': self._get_header_value(headers, 'From'),
                'To': self._get_header_value(headers, 'To'),
                'Date': self._get_header_value(headers, 'Date'),
                'Message-ID': self._get_header_value(headers, 'Message-ID'),
                'In-Reply-To': self._get_header_value(headers, 'In-Reply-To'),
                'References': self._get_header_value(headers, 'References'),
            },
            'body_plain_text': self._get_message_body(payload),
            'replies': []
        }
        return parsed_data

    def _build_thread_hierarchy(self, messages_raw):
        """
        Builds a hierarchical structure of messages within a thread based on
        In-Reply-To and References headers.
        """
        if not messages_raw:
            return []

        parsed_messages = [self._parse_message_data(msg) for msg in messages_raw]
        message_map = {msg['headers']['Message-ID']: msg for msg in parsed_messages if msg['headers']['Message-ID']}

        root_messages = []

        for msg in parsed_messages:
            in_reply_to_id = msg['headers'].get('In-Reply-To')
            if in_reply_to_id:
                in_reply_to_id = in_reply_to_id.strip('<>')

            parent_msg = None
            if in_reply_to_id and in_reply_to_id in message_map:
                parent_msg = message_map[in_reply_to_id]

            if parent_msg:
                parent_msg['replies'].append(msg)
            else:
                root_messages.append(msg)

        for msg in parsed_messages:
            if 'replies' in msg:
                msg['replies'].sort(key=lambda x: int(x.get('internalDate', 0)))

        root_messages.sort(key=lambda x: int(x.get('internalDate', 0)))

        return root_messages

    def get_email_by_sender_and_date(self, sender_email, date_string_input, lang='en', max_results=1):
        """
        Fetches an email based on sender and a specific date, handling various input date formats.
        """
        if not self.service:
            print("Error: Gmail service not connected. Call .connect() first.")
            return None

        formatted_date = self._parse_date_to_gmail_format(date_string_input, lang)
        if not formatted_date:
            return None

        try:
            start_date_obj = parser.parse(date_string_input)
            end_date_obj = start_date_obj + timedelta(days=1)
            query_after = start_date_obj.strftime('%Y/%m/%d')
            query_before = end_date_obj.strftime('%Y/%m/%d')
        except ValueError:
            print(f"Error parsing date for range: {date_string_input}")
            return None

        query = f"from:{sender_email} after:{query_after} before:{query_before}"

        try:
            response = self.service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
            messages = response.get('messages', [])

            if not messages:
                print(f"No messages found for query: '{query}'")
                return None

            message_id = messages[0]['id']
            full_message = self.service.users().messages().get(userId='me', id=message_id, format='full').execute()

            return self._parse_message_data(full_message)

        except HttpError as error:
            print(f"An API error occurred: {error}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

    def get_thread_messages(self, thread_id):
        """
        Fetches all messages within a specific Gmail thread and returns them
        in a hierarchical dictionary structure.
        """
        if not self.service:
            print("Error: Gmail service not connected.")
            return None

        try:
            thread = self.service.users().threads().get(userId='me', id=thread_id, format='full').execute()

            messages_in_thread_raw = thread.get('messages', [])
            print(f"Thread '{thread_id}' contains {len(messages_in_thread_raw)} raw messages.")

            hierarchical_messages = self._build_thread_hierarchy(messages_in_thread_raw)
            return hierarchical_messages

        except HttpError as error:
            print(f"An API error occurred while fetching thread: {error}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

    def get_thread_id_by_sender_and_date(self, sender_email, date_string_input, lang='en'):
        """
        Fetches the thread ID of a message based on sender and a specific date.
        """
        if not self.service:
            print("Error: Gmail service not connected. Call .connect() first.")
            return None

        formatted_date = self._parse_date_to_gmail_format(date_string_input, lang)
        if not formatted_date:
            return None

        try:
            start_date_obj = parser.parse(date_string_input)
            end_date_obj = start_date_obj + timedelta(days=1)
            query_after = start_date_obj.strftime('%Y/%m/%d')
            query_before = end_date_obj.strftime('%Y/%m/%d')
        except ValueError:
            print(f"Error parsing date for range: {date_string_input}")
            return None

        query = f"from:{sender_email} after:{query_after} before:{query_before}"

        try:
            response = self.service.users().messages().list(userId='me', q=query, maxResults=1).execute()
            messages = response.get('messages', [])

            if not messages:
                print(f"No message found for sender '{sender_email}' on date '{date_string_input}'.")
                return None

            thread_id = messages[0]['threadId']
            print(f"Found thread ID '{thread_id}' for a message from '{sender_email}' on '{date_string_input}'.")
            return thread_id

        except HttpError as error:
            print(f"An API error occurred: {error}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

    def download_eml_file(self, message_id, file_path):
        """
        Downloads a single email message as an .eml file.
        """
        if not self.service:
            print("Error: Gmail service not connected. Call .connect() first.")
            return False

        try:
            message = self.service.users().messages().get(userId='me', id=message_id, format='raw').execute()
            raw_data = message['raw']
            decoded_data = base64.urlsafe_b64decode(raw_data + '==')

            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'wb') as f:
                f.write(decoded_data)

            print(f"Successfully downloaded message '{message_id}' to '{file_path}'")
            return True

        except HttpError as error:
            print(f"An API error occurred while downloading message {message_id}: {error}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred while downloading message {message_id}: {e}")
            return False

    def search_and_download_eml(self, emails_list, search_string, download_base_dir):
        """
        Recursively searches for a string in email bodies within a hierarchical list
        of email dictionaries and downloads matching emails as .eml files.

        Args:
            emails_list (list): The list of email dictionaries (can be hierarchical).
            search_string (str): The string to search for in the email body (case-insensitive).
            download_base_dir (str): The base directory where .eml files will be saved.

        Returns:
            int: The count of emails found and attempted to download.
        """
        found_count = 0
        os.makedirs(download_base_dir, exist_ok=True)  # Ensure the directory exists

        for email in emails_list:
            body = email['body_plain_text']

            if body and search_string.lower() in body.lower():
                found_count += 1
                print(f"\nMatch found in message ID: {email['id']}")
                print(f"  Subject: {email['headers'].get('Subject', 'N/A')}")
                print(f"  Snippet: {email['snippet']}")

                subject = email['headers'].get('Subject', 'No_Subject')
                # Basic filename sanitization: remove common invalid characters for filenames
                sanitized_subject = "".join([c for c in subject if c.isalnum() or c in (' ', '.', '-', '_')]).strip()
                if not sanitized_subject:
                    sanitized_subject = "No_Subject"

                filename = f"{email['id']}_{sanitized_subject[:50]}.eml"  # Limit subject length for filename
                file_path = os.path.join(download_base_dir, filename)

                if self.download_eml_file(email['id'], file_path):
                    print(f"  Downloaded to: {file_path}")
                else:
                    print(f"  Failed to download: {file_path}")

            if email['replies']:
                found_count += self.search_and_download_eml(email['replies'], search_string, download_base_dir)

        return found_count