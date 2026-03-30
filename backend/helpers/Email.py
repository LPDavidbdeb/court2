import os
import base64
import re
from email.header import decode_header, make_header
from dateutil import parser


class Email:
    """
    Represents a single email message with parsed attributes and methods for searching/saving.
    It is designed to be source-agnostic, tracking its origin via a 'source' attribute.
    """

    def __init__(self, raw_message_data: dict, dao_instance: object,
                 source: str = "unknown"):  # dao_instance type changed to 'object' for generality
        """
        Initializes an Email object from raw API message data.

        Args:
            raw_message_data (dict): The raw dictionary returned by a specific API for a message.
            dao_instance (object): An instance of the relevant Data Access Object (e.g., GmailDAO)
                                   to perform API operations specific to this email\'s source (like downloading EML).
            source (str): A string indicating the origin of this email (e.g., "gmail", "icloud").
        """
        self._raw_data = raw_message_data  # Keep raw data for debugging/completeness if needed
        self._dao = dao_instance  # Store DAO instance for source-specific operations
        self.source = source  # NEW: Store the source of this email

        # Core email attributes (should be consistent across sources)
        self.id = raw_message_data.get('id')
        self.thread_id = raw_message_data.get('threadId')
        self.snippet = raw_message_data.get('snippet')
        self.history_id = raw_message_data.get('historyId')
        self.internal_date = raw_message_data.get('internalDate')  # Unix timestamp in milliseconds

        payload = raw_message_data.get('payload', {})
        headers = payload.get('headers', [])

        # Parse headers (helper method remains generic)
        self.headers = {
            'Subject': self._get_header_value(headers, 'Subject'),
            'From': self._get_header_value(headers, 'From'),
            'To': self._get_header_value(headers, 'To'),
            'Cc': self._get_header_value(headers, 'Cc'),
            'Date': self._get_header_value(headers, 'Date'),
            'Message-ID': self._get_header_value(headers, 'Message-ID'),
            'In-Reply-To': self._get_header_value(headers, 'In-Reply-To'),
            'References': self._get_header_value(headers, 'References'),
        }

        # Extract and decode body content (helper method remains generic)
        self.body_plain_text = self._get_message_body(payload)
        print(f"Extracted body for email {self.id}: {self.body_plain_text}")

        self.replies = []  # Placeholder for hierarchical structure in Thread

    def _get_header_value(self, headers, name):
        """Helper to get a header value from raw headers, handling potential encoding."""
        for header in headers:
            if header['name'].lower() == name.lower():
                return str(make_header(decode_header(header['value'])))
        return None

    def _get_message_body(self, payload):
        """
        Extracts and decodes the plain text or HTML body from a message payload.
        Prioritizes plain text over HTML by searching through all MIME parts.
        """
        # For multipart messages, we need to search for the best part.
        if 'parts' in payload:
            # First, search for a plain text part recursively.
            queue = list(payload.get('parts', []))
            while queue:
                part = queue.pop(0)
                if 'parts' in part:
                    # This is a multipart part, add its children to the queue
                    queue.extend(part['parts'])
                    continue
                
                mime_type = part.get('mimeType')
                if mime_type == 'text/plain' and 'body' in part and 'data' in part['body']:
                    return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')

            # If no plain text was found, search for an HTML part.
            queue = list(payload.get('parts', []))
            while queue:
                part = queue.pop(0)
                if 'parts' in part:
                    queue.extend(part['parts'])
                    continue

                mime_type = part.get('mimeType')
                if mime_type == 'text/html' and 'body' in part and 'data' in part['body']:
                    return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
            
            return None # No text or html body found in parts

        # For single-part messages
        elif 'body' in payload and 'data' in payload['body']:
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
        
        return None

    def search_string(self, search_term: str, case_sensitive: bool = False) -> bool:
        """
        Checks if the email\'s plain text body contains the search string.
        This method is generic to any email with a body_plain_text attribute.
        """
        if not self.body_plain_text:
            return False

        target_body = self.body_plain_text if case_sensitive else self.body_plain_text.lower()
        target_search_term = search_term if case_sensitive else search_term.lower()

        return target_search_term in target_body

    def _get_initial(self, name_or_email_string):
        """
        Extracts the first letter of the "name" part (if available) or the local part
        of the email address from a 'From' or 'To' string for filename generation.
        Returns 'X' if no suitable initial can be extracted.
        """
        if not name_or_email_string:
            return "X"  # Placeholder for missing info

        # Try to extract display name in quotes (e.g., "John Doe" <email>)
        match_quoted_name = re.search(r'^"([^\"]+)"', name_or_email_string)
        if match_quoted_name:
            name_part = match_quoted_name.group(1).strip()
            if name_part:
                return name_part[0].upper()

        # Try to extract display name before an angle bracket (e.g., John Doe <email>)
        match_unquoted_name = re.search(r'([^<]+)\\s*<', name_or_email_string)
        if match_unquoted_name:
            name_part = match_unquoted_name.group(1).strip()
            if name_part:
                return name_part[0].upper()

        # Fallback: Extract email address from <email@domain.com>
        email_match = re.search(r'<([^>]+)>', name_or_email_string)
        if email_match:
            email_address = email_match.group(1)
            local_part = email_address.split('@')[0]
            if local_part:
                return local_part[0].upper()

        # Last resort: Take first char of the whole string, if it\'s not an empty string
        if name_or_email_string:
            return name_or_email_string[0].upper()

        return "X"  # Still nothing useful

    def _sanitize_filename_part(self, text, max_length=50):
        """
        Sanitizes a string to be safe for use in a filename.
        Removes invalid characters and truncates to a max length.
        """
        if not text:
            return "N_A"
        # Replace any character that is not a word character, a dot, or a dash with an underscore.
        # Note: \s (whitespace) is NOT included in the whitelist, so it will be replaced.
        sanitized = re.sub(r'[^\w.-]', '_', text)
        # Collapse sequences of one or more underscores.
        sanitized = re.sub(r'[_]+', '_', sanitized)
        return sanitized[:max_length].strip('_')

    def save_eml(self, base_download_dir="DL"):
        """
        Saves this email message as an .eml file to a structured directory
        with a descriptive filename.

        Args:
            base_download_dir (str): The root directory where DL/Email/ will be created.
                                     Defaults to "DL".

        Returns:
            str|None: The full path to the saved file if successful, otherwise None.
        """
        if not self._dao:
            print(f"Error: Email object (source: {self.source}) not initialized with a DAO instance. Cannot save EML.")
            return None

        # 1. Construct the target directory: DL/Email/source
        target_directory = os.path.join(base_download_dir, "Email", self.source)
        os.makedirs(target_directory, exist_ok=True)  # Ensure directory exists

        # 2. Generate the dynamic filename: YYYYMMDD_sender_initial_receiver_initial_subject.eml

        # Date (YYYYMMDD)
        try:
            date_obj = parser.parse(self.headers.get('Date', ''))
            date_part = date_obj.strftime('%Y%m%d')
        except (ValueError, TypeError):
            date_part = "YYYYMMDD"  # Fallback if date parsing fails

        # Sender Initial
        sender_initial = self._get_initial(self.headers.get('From', ''))

        # Receiver Initial (from 'To' header)
        receiver_initial = self._get_initial(self.headers.get('To', ''))

        # Subject (sanitized)
        subject_part = self._sanitize_filename_part(self.headers.get('Subject', 'No_Subject'),
                                                    max_length=100)  # Longer subject part allowed

        filename = f"{date_part}_{sender_initial}_{receiver_initial}_{subject_part}.eml"
        full_file_path = os.path.join(target_directory, filename)

        # 3. Call the DAO\'s download method
        try:
            if hasattr(self._dao, 'download_raw_eml_file'):
                success = self._dao.download_raw_eml_file(self.id, full_file_path)
                if success:
                    print(f"Successfully saved EML for message ID {self.id} to: {full_file_path}")
                    return full_file_path
                return None
            else:
                print(f"Error: DAO for source \'{self.source}\' does not have a \'download_raw_eml_file\' method.")
                return None
        except Exception as e:
            print(f"Error saving EML for message ID {self.id} (source: {self.source}): {e}")
            return None

    def __repr__(self):
        return f"Email(id=\'{self.id}\', Subject=\'{self.headers.get('Subject', 'N/A')}\', Source=\'{self.source}\')"

    def __str__(self):
        return (f"Subject: {self.headers.get('Subject', 'N/A')}\\n"
                f"From: {self.headers.get('From', 'N/A')}\\n"
                f"To: {self.headers.get('To', 'N/A')}\\n"
                f"Date: {self.headers.get('Date', 'N/A')}\\n"
                f"Source: {self.source}\\n"  # Include source in string representation
                f"Snippet: {self.snippet}\\n"
                f"Body (first 100 chars): {self.body_plain_text[:100] if self.body_plain_text else 'N/A'}...")
