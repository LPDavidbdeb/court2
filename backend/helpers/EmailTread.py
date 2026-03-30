from helpers.Email import Email

class EmailThread:
    """
    Represents an email thread, containing a hierarchical structure of Email objects.
    It is designed to be source-agnostic, tracking its origin via a 'source' attribute.
    """

    def __init__(self, raw_thread_messages: list, dao_instance: object,
                 source: str = "unknown"):  # dao_instance type changed to 'object' for generality
        self._dao = dao_instance
        self.source = source
        self.thread_id = None
        if raw_thread_messages:
            self.thread_id = raw_thread_messages[0].get('threadId')

        self.messages = self._build_hierarchy(raw_thread_messages)

    def _build_hierarchy(self, raw_messages: list) -> list[Email]:
        """
        Builds a hierarchical structure of Email objects based on In-Reply-To and References headers.
        This version correctly handles complex threading, out-of-order messages, and missing headers.
        """
        if not raw_messages:
            return []

        # Step 1: Create email objects and a lookup map by Message-ID header
        all_emails = []
        emails_by_header_id = {}
        for msg_data in raw_messages:
            email = Email(msg_data, self._dao, self.source)
            email.replies = []  # Ensure replies list is clean
            all_emails.append(email)
            msg_id_header = email.headers.get('Message-ID')
            if msg_id_header:
                emails_by_header_id[msg_id_header.strip('<>').lower()] = email

        # Step 2: Link emails into a hierarchy
        for email in all_emails:
            parent_id_to_find = None

            # Try to find a parent using the In-Reply-To header first
            in_reply_to = email.headers.get('In-Reply-To')
            if in_reply_to:
                parent_id_to_find = in_reply_to.strip('<>').lower()

            # If not found, fall back to the References header
            if not parent_id_to_find or parent_id_to_find not in emails_by_header_id:
                references_header = email.headers.get('References')
                if references_header:
                    # The parent is the last valid reference in the list
                    ref_ids = [ref.strip('<>').lower() for ref in references_header.split()]
                    for ref_id in reversed(ref_ids):
                        if ref_id in emails_by_header_id:
                            parent_id_to_find = ref_id
                            break
            
            # If we found a valid parent ID, link the child
            if parent_id_to_find and parent_id_to_find in emails_by_header_id:
                parent = emails_by_header_id[parent_id_to_find]
                if email not in parent.replies:
                    parent.replies.append(email)
    
        # Step 3: Identify root messages (those not in any 'replies' list)
        all_replies = {reply for email in all_emails for reply in email.replies}
        root_messages = [email for email in all_emails if email not in all_replies]

        # Step 4: Sort all levels of the hierarchy by date
        def sort_recursively(messages):
            messages.sort(key=lambda m: int(m.internal_date or 0))
            for message in messages:
                if message.replies:
                    sort_recursively(message.replies)

        sort_recursively(root_messages)
        return root_messages

    def get_flattened_thread(self) -> list[Email]:
        """
        Returns a flat list of all emails in the thread, with an added 'indent_level' 
        attribute to indicate the reply depth.
        """
        flattened_list = []

        def _flatten(messages, level):
            # Sort messages by date before flattening to ensure chronological order
            messages.sort(key=lambda x: int(x.internal_date or 0))
            for msg in messages:
                msg.indent_level = level
                flattened_list.append(msg)
                if msg.replies:
                    _flatten(msg.replies, level + 1)

        _flatten(self.messages, 0)
        return flattened_list

    def find_emails_by_string(self, search_term: str, case_sensitive: bool = False) -> list[Email]:
        """
        Searches the entire flattened thread for a string and returns matching Email objects.
        """
        matching_emails = []
        for email_obj in self.get_flattened_thread():
            if email_obj.search_string(search_term, case_sensitive):
                matching_emails.append(email_obj)
        return matching_emails