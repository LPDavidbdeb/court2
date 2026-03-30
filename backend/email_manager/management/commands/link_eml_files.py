import os
import email
from email import policy
from email.parser import BytesParser
from django.core.management.base import BaseCommand
from email_manager.models import Email

class Command(BaseCommand):
    help = 'Links .eml files by finding the Gmail-specific ID in the headers.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting to link .eml files by Gmail ID header..."))

        base_eml_dir = os.path.join("DL", "Email", "Email", "gmail")
        if not os.path.isdir(base_eml_dir):
            self.stderr.write(self.style.ERROR(f"EML directory not found at: {base_eml_dir}"))
            return

        # Get all emails that need a path and map their message_id for quick lookup
        emails_to_update = {e.message_id: e for e in Email.objects.filter(eml_file_path__isnull=True)}
        if not emails_to_update:
            self.stdout.write(self.style.SUCCESS("No emails found with a missing eml_file_path."))
            return

        self.stdout.write(f"Found {len(emails_to_update)} DB records that need linking.")

        linked_count = 0
        unmatched_files = 0
        already_linked_or_not_in_db = 0

        # The specific, non-standard header Gmail uses for its internal message ID.
        GMAIL_ID_HEADER = 'X-Gm-Message-Id'

        for filename in os.listdir(base_eml_dir):
            if not filename.endswith('.eml'):
                continue

            full_path = os.path.join(base_eml_dir, filename)
            try:
                with open(full_path, 'rb') as f:
                    msg = BytesParser(policy=policy.default).parse(f)
                
                gmail_id = msg.get(GMAIL_ID_HEADER)
                
                if not gmail_id:
                    self.stdout.write(self.style.WARNING(f"  - No '{GMAIL_ID_HEADER}' header in {filename}"))
                    unmatched_files += 1
                    continue

                gmail_id = gmail_id.strip()

                # Check if this gmail_id is one of the records we need to update
                if gmail_id in emails_to_update:
                    email_record = emails_to_update[gmail_id]
                    
                    email_record.eml_file_path = full_path
                    email_record.save(update_fields=['eml_file_path'])
                    
                    self.stdout.write(self.style.SUCCESS(f"  - Linked {filename} to DB record for ID {gmail_id}"))
                    linked_count += 1
                    
                    # Remove from the dict to prevent re-linking and to count remaining
                    del emails_to_update[gmail_id]
                else:
                    # This file's ID corresponds to a DB entry that is already linked or doesn't exist.
                    already_linked_or_not_in_db += 1

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"An error occurred while processing {filename}: {e}"))
                unmatched_files += 1

        self.stdout.write(self.style.SUCCESS(f"\nLinking complete."))
        self.stdout.write(f"- Successfully linked {linked_count} new .eml files.")
        self.stdout.write(f"- Found {already_linked_or_not_in_db} files that were already linked or not in the target DB set.")
        self.stdout.write(f"- Could not match {unmatched_files} files (missing the required Gmail ID header).")
        
        if emails_to_update:
            self.stdout.write(self.style.WARNING(f"\nCould not find matching files for {len(emails_to_update)} DB records:"))
            for email_record in emails_to_update.values():
                self.stdout.write(f"  - PK: {email_record.pk}, Subject: '{email_record.subject}'")
