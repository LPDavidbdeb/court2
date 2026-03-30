import os
import base64
import re
from email.header import decode_header, make_header
from dateutil import parser
from bs4 import BeautifulSoup # NOUVEAU: Importez BeautifulSoup


class Email:
    """
    Represents a single email message with parsed attributes and methods for searching/saving.
    It is designed to be source-agnostic, tracking its origin via a 'source' attribute.
    """

    def __init__(self, raw_message_data: dict, dao_instance: object,
                 source: str = "unknown"):  # dao_instance type changed to 'object' for generality
        """
        Initializes an Email object from raw API message data.
        """
        self._raw_data = raw_message_data
        self._dao = dao_instance
        self.source = source

        self.id = raw_message_data.get('id')
        self.thread_id = raw_message_data.get('threadId')
        self.snippet = raw_message_data.get('snippet')
        self.history_id = raw_message_data.get('historyId')
        self.internal_date = raw_message_data.get('internalDate')

        payload = raw_message_data.get('payload', {})
        headers = payload.get('headers', [])

        self.headers = {
            'Subject': self._get_header_value(headers, 'Subject'),
            'From': self._get_header_value(headers, 'From'),
            'To': self._get_header_value(headers, 'To'),
            'Cc': self._get_header_value(headers, 'Cc'),
            'Bcc': self._get_header_value(headers, 'Bcc'),
            'Date': self._get_header_value(headers, 'Date'),
            'Message-ID': self._get_header_value(headers, 'Message-ID'),
            'In-Reply-To': self._get_header_value(headers, 'In-Reply-To'),
            'References': self._get_header_value(headers, 'References'),
        }

        self.body_plain_text = self._get_message_body(payload)
        self.body_cleaned = self._clean_body_of_replies(self.body_plain_text) # NEW

        self.replies = []

    def get_date_sent(self):
        """
        Parses the 'Date' header and returns a datetime object.
        Returns None if the date cannot be parsed.
        This version uses fuzzy parsing to handle a wider variety of date formats.
        """
        date_str = self.headers.get('Date')
        if not date_str:
            return None
        try:
            # Use fuzzy parsing to ignore surrounding text that is not part of the date
            return parser.parse(date_str, fuzzy=True)
        except (ValueError, TypeError, parser.ParserError):
            # If parsing fails, return None so the template can handle it
            return None

    def _get_header_value(self, headers, name):
        """Helper to get a header value from raw headers, handling potential encoding."""
        for header in headers:
            if header['name'].lower() == name.lower():
                return str(make_header(decode_header(header['value'])))
        return None

    def _extract_emails_from_header(self, header_string):
        """Helper to extract all email addresses from a header string (e.g., 'To', 'Cc', 'From')."""
        if not header_string:
            return []
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', header_string)
        return list(set(emails))

    def get_all_participant_emails(self) -> list[str]:
        """
        Extracts all unique email addresses from 'From', 'To', 'Cc', and 'Bcc' headers.
        """
        all_emails = set()
        for header in ['From', 'To', 'Cc', 'Bcc']:
            header_content = self.headers.get(header)
            if header_content:
                all_emails.update(self._extract_emails_from_header(header_content))
        return list(all_emails)

    def _get_message_body(self, payload):
        """
        Extracts and decodes the plain text or HTML body from a message payload.
        Prioritizes plain text, then attempts to parse HTML if no plain text is found.
        """
        body_data = None
        
        # 1. Rechercher d'abord le contenu en texte brut
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain' and 'body' in part and 'data' in part['body']:
                    body_data = part['body']['data']
                    return base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
            # Si le texte brut n'a pas été trouvé, vérifier de manière récursive
            for part in payload['parts']:
                nested_body = self._get_message_body(part)
                if nested_body:
                    return nested_body
        
        # 2. Si aucun texte brut n'est trouvé, rechercher le contenu HTML
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/html' and 'body' in part and 'data' in part['body']:
                    body_data = part['body']['data']
                    html_body = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
                    # Utiliser BeautifulSoup pour extraire le texte de l'HTML
                    soup = BeautifulSoup(html_body, 'html.parser')
                    return soup.get_text(separator=' ', strip=True)

        # 3. Gérer le cas où le corps de l'e-mail n'a pas de parties (contenu direct)
        if 'body' in payload and 'data' in payload['body']:
            body_data = payload['body']['data']
            return base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
            
        return None

    def _clean_body_of_replies(self, text_body):
        """
        Removes quoted replies and signatures from the email body.
        This version is more robust for different languages and formats.
        """
        if not text_body:
            return ""

        # Split the body into lines
        lines = text_body.splitlines()
        
        cleaned_lines = []
        
        # This regex is more robust. It looks for common reply headers in English and French,
        # as well as lines that are clearly part of a signature or a forwarded message block.
        # It also handles lines starting with >
        reply_pattern = re.compile(
            r"^(>|On\s.+|Le\s.+|From:|Sent:|De\s?:|Envoyé\s?:|--|\s*_)", 
            re.IGNORECASE
        )

        # Iterate backwards from the end of the email
        for line in reversed(lines):
            # If we find a line that looks like a reply/forward header, we stop.
            if reply_pattern.search(line):
                break
            cleaned_lines.append(line)
        
        # The actual message is what we have before the reply starts.
        # So we reverse the cleaned_lines back to the original order.
        cleaned_lines.reverse()
        
        # Fallback: If the above logic results in an empty message,
        # it might be a simple top-reply. Let's try a simpler approach.
        if not cleaned_lines:
            for line in lines:
                if reply_pattern.search(line):
                    break
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip()

    def search_string(self, search_term: str, case_sensitive: bool = False) -> bool:
        """
        Checks if the email's CLEANED body contains the search string.
        """
        if not self.body_cleaned:
            return False

        target_body = self.body_cleaned if case_sensitive else self.body_cleaned.lower()
        target_search_term = search_term if case_sensitive else search_term.lower()

        return target_search_term in target_body

    def _get_initial(self, name_or_email_string):
        if not name_or_email_string:
            return "X"
        match_quoted_name = re.search(r'^"([^"]+)"', name_or_email_string)
        if match_quoted_name:
            name_part = match_quoted_name.group(1).strip()
            if name_part:
                return name_part[0].upper()
        match_unquoted_name = re.search(r'([^<]+)\s*<', name_or_email_string)
        if match_unquoted_name:
            name_part = match_unquoted_name.group(1).strip()
            if name_part:
                return name_part[0].upper()
        email_match = re.search(r'<([^>]+)>', name_or_email_string)
        if email_match:
            email_address = email_match.group(1)
            local_part = email_address.split('@')[0]
            if local_part:
                return local_part[0].upper()
        if name_or_email_string:
            return name_or_email_string[0].upper()
        return "X"

    def _sanitize_filename_part(self, text, max_length=50):
        if not text:
            return "N_A"
        sanitized = re.sub(r'[^\w\s\.-_]', '_', text)
        sanitized = sanitized.strip()
        sanitized = re.sub(r'[_\s\.-_]+', '_', sanitized)
        return sanitized[:max_length].strip('_') if sanitized else "N_A"

    def save_eml(self, base_download_dir="DL") -> bool:
        if not self._dao:
            print(f"Error: Email object (source: {self.source}) not initialized with a DAO instance. Cannot save EML.")
            return False
        target_directory = os.path.join(base_download_dir, "Email", self.source)
        os.makedirs(target_directory, exist_ok=True)
        try:
            date_obj = parser.parse(self.headers.get('Date', ''))
            date_part = date_obj.strftime('%Y%m%d')
        except (ValueError, TypeError):
            date_part = "YYYYMMDD"
        sender_initial = self._get_initial(self.headers.get('From', ''))
        receiver_initial = self._get_initial(self.headers.get('To', ''))
        subject_part = self._sanitize_filename_part(self.headers.get('Subject', 'No_Subject'), max_length=100)
        filename = f"{date_part}_{sender_initial}_{receiver_initial}_{subject_part}.eml"
        full_file_path = os.path.join(target_directory, filename)
        try:
            if hasattr(self._dao, 'download_raw_eml_file'):
                success = self._dao.download_raw_eml_file(self.id, full_file_path)
                if success:
                    print(f"Successfully saved EML for message ID {self.id} to: {full_file_path}")
                return success
            else:
                print(f"Warning: DAO for source '{self.source}' does not have a 'download_raw_eml_file' method. Assuming file saving is handled externally.")
                return True
        except Exception as e:
            print(f"Error saving EML for message ID {self.id} (source: {self.source}): {e}")
            return False

    def __repr__(self):
        return f"Email(id='{self.id}', Subject='{self.headers.get('Subject', 'N/A')}', Source='{self.source}')"

    def __str__(self):
        return (f"Subject: {self.headers.get('Subject', 'N/A')}\n"
                f"From: {self.headers.get('From', 'N/A')}\n"
                f"To: {self.headers.get('To', 'N/A')}\n"
                f"Date: {self.headers.get('Date', 'N/A')}\n"
                f"Source: {self.source}\n"
                f"Snippet: {self.snippet}\n"
                f"Body (first 100 chars): {self.body_plain_text[:100] if self.body_plain_text else 'N/A'}...")
