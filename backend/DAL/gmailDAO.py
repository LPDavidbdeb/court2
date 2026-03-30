import base64
import os.path
import json
from datetime import datetime, timedelta
from dateutil import parser
import locale

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.conf import settings

# Keep scopes as they are
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


class ThreadNotFoundError(Exception):
    """Custom exception raised when a Gmail thread is not found."""
    pass


class GmailDAO:
    """
    Data Access Object (DAO) for interacting with the Gmail API.
    Handles authentication and fetches raw email/thread data.
    It does NOT process or structure the data beyond raw API responses.
    """

    def __init__(self):
        """
        Initializes the DAO, setting paths for credentials from Django settings.
        """
        self.client_secret_path = settings.GMAIL_API_CREDENTIALS_FILE
        self.token_path = settings.GMAIL_TOKEN_FILE # New: Get token path from settings
        self.service = None

    def connect(self):
        """
        Handles the OAuth 2.0 authentication flow and builds the Gmail API service object.
        Returns the authenticated Gmail API service object, or None if connection fails.
        """
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
                # Ensure the directory for the token exists
                os.makedirs(os.path.dirname(self.token_path), exist_ok=True)
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
            print(f"An unexpected error occurred: {e}")
            return None

    def _parse_date_to_gmail_format(self, date_string, lang='en'):
        """
        Parses a date string (English or French) into 'YYYY/MM/DD' format.
        This remains in DAO as it's a utility for building API queries.
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

    def get_raw_message(self, message_id):
        """
        Fetches a single raw email message from the Gmail API.
        Returns the raw API message dictionary, or None if not found.
        """
        if not self.service:
            print("Error: Gmail service not connected. Call .connect() first.")
            return None
        try:
            full_message = self.service.users().messages().get(userId='me', id=message_id, format='full').execute()
            return full_message
        except HttpError as error:
            print(f"An API error occurred while fetching message {message_id}: {error}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred while fetching message {message_id}: {e}")
            return None

    def get_raw_thread_messages(self, thread_id):
        """
        Fetches all raw messages within a specific Gmail thread from the API.
        Returns a list of raw API message dictionaries.
        Raises ThreadNotFoundError if the thread doesn't exist.
        Returns None for other connection errors.
        """
        if not self.service:
            print("Error: Gmail service not connected. Call .connect() first.")
            return None
        try:
            thread = self.service.users().threads().get(userId='me', id=thread_id, format='full').execute()
            messages_in_thread_raw = thread.get('messages', [])
            return messages_in_thread_raw
        except HttpError as error:
            if error.resp.status == 404:
                raise ThreadNotFoundError(f"No thread found with ID {thread_id}")
            else:
                print(f"An API error occurred while fetching thread {thread_id}: {error}")
                return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

    def get_thread_ids_by_participant_and_date(self, participant_email, date_string_input, lang='en'):
        """
        Fetches all unique thread IDs of messages based on a participant's email
        and a specific date.
        Returns a list of unique thread IDs, or an empty list.
        """
        if not self.service:
            print("Error: Gmail service not connected. Call .connect() first.")
            return []

        try:
            start_date_obj = parser.parse(date_string_input)
            end_date_obj = start_date_obj + timedelta(days=1)
            query_after = start_date_obj.strftime('%Y/%m/%d')
            query_before = end_date_obj.strftime('%Y/%m/%d')
        except ValueError:
            print(f"Error parsing date for range: {date_string_input}")
            return []

        query = (
            f"(from:{participant_email} OR to:{participant_email} OR cc:{participant_email} OR bcc:{participant_email}) "
            f"after:{query_after} before:{query_before}"
        )
        print(f"Constructed Gmail query: '{query}'")

        try:
            response = self.service.users().messages().list(userId='me', q=query).execute()
            messages = response.get('messages', [])

            if not messages:
                print(f"No messages found involving '{participant_email}' on date '{date_string_input}'.")
                return []

            thread_ids = {message['threadId'] for message in messages}
            print(f"Found {len(thread_ids)} unique thread(s) for messages involving '{participant_email}' on '{date_string_input}'.")
            return list(thread_ids)

        except HttpError as error:
            print(f"An API error occurred: {error}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return []

    def find_message_id_by_criteria(self, participant_email, date_string_input, excerpt, lang='en'):
        """
        Finds a specific message ID based on participant, date, and a text excerpt.
        This is a more precise search than get_thread_id_by_participant_and_date.
        Returns a dictionary {'message_id': '...', 'thread_id': '...'} or None.
        """
        if not self.service:
            print("Error: Gmail service not connected. Call .connect() first.")
            return None

        try:
            start_date_obj = parser.parse(date_string_input)
            end_date_obj = start_date_obj + timedelta(days=1)
            query_after = start_date_obj.strftime('%Y/%m/%d')
            query_before = end_date_obj.strftime('%Y/%m/%d')
        except ValueError:
            print(f"Error parsing date for range: {date_string_input}")
            return None

        # Construct a more precise query including the excerpt
        query = (
            f'(from:{participant_email} OR to:{participant_email} OR cc:{participant_email} OR bcc:{participant_email}) '
            f'after:{query_after} before:{query_before} "{excerpt}"'
        )
        print(f"Constructed precise Gmail query: '{query}'")

        try:
            response = self.service.users().messages().list(userId='me', q=query, maxResults=1).execute()
            messages = response.get('messages', [])

            if not messages:
                print(f"No message found from '{participant_email}' on '{date_string_input}' containing the excerpt.")
                return None

            message_id = messages[0]['id']
            thread_id = messages[0]['threadId']
            print(f"Found message ID '{message_id}' in thread '{thread_id}'.")
            return {'message_id': message_id, 'thread_id': thread_id}

        except HttpError as error:
            print(f"An API error occurred: {error}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

    def download_raw_eml_file(self, message_id, file_path):
        """
        Downloads a single email message as an .eml file directly from the API's raw format.
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

            print(f"Successfully downloaded raw message '{message_id}' to '{file_path}'")
            return True

        except HttpError as error:
            print(f"An API error occurred while downloading message {message_id}: {error}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred while downloading message {message_id}: {e}")
            return False