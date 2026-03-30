import os
import base64
import email

class EmlFileDAO:
    """
    Data Access Object (DAO) for handling email files and parsing raw email data.
    """

    def get_raw_eml_content(self, file_path: str) -> bytes | None:
        """
        Reads the raw content of an .eml file from the local system.
        """
        if not os.path.exists(file_path):
            print(f"Error: EML file not found at {file_path}")
            return None
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except IOError as e:
            print(f"Error reading EML file {file_path}: {e}")
            return None

    @staticmethod
    def parse_raw_message_data(raw_msg: dict) -> dict:
        """
        Parses the raw message dictionary from the Gmail API into a cleaner format.
        This is a static method because it operates on data, not an instance.
        """
        message_data = {
            'id': raw_msg.get('id'),
            'thread_id': raw_msg.get('threadId'),
            'headers': {},
            'body_plain_text': ''
        }

        payload = raw_msg.get('payload', {})
        if not payload:
            return message_data

        # Extract headers into a simple dictionary
        headers = payload.get('headers', [])
        for header in headers:
            message_data['headers'][header['name']] = header['value']

        # Find the plain text body, searching recursively through multipart messages
        body_plain_text = None

        def find_part(parts):
            """Recursively search for the plain text part."""
            for part in parts:
                if part.get('mimeType') == 'text/plain' and 'data' in part.get('body', {}):
                    return part['body']
                if 'parts' in part:
                    found_part = find_part(part['parts'])
                    if found_part:
                        return found_part
            return None

        body_part_body = None
        if 'parts' in payload:
            body_part_body = find_part(payload['parts'])

        if body_part_body and 'data' in body_part_body:
            body_data = body_part_body['data']
            body_plain_text = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
        # Fallback for non-multipart messages or if recursive search fails
        elif 'body' in payload and 'data' in payload['body']:
            body_data = payload['body']['data']
            body_plain_text = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')

        message_data['body_plain_text'] = body_plain_text or "(No body content available)"
        return message_data
