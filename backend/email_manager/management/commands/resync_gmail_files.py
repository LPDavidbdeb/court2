import os
from django.core.management.base import BaseCommand
from django.db import transaction
from email_manager.models import Email
from DAL.gmailDAO import GmailDAO
from helpers.Email import Email as EmailHelper # The helper class

class Command(BaseCommand):
    help = 'Resyncs all Gmail records with the server, creating unique .eml files for each message.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting resynchronization of all Gmail records..."))

        # Initialize the DAO
        dao = GmailDAO()
        if not dao.connect():
            self.stdout.write(self.style.ERROR("Failed to connect to Gmail API. Aborting."))
            return

        # Get all emails from the Gmail source
        emails_to_resync = Email.objects.filter(dao_source='gmail')
        total_emails = emails_to_resync.count()
        self.stdout.write(f"Found {total_emails} Gmail records to process.")

        success_count = 0
        failed_count = 0

        for i, email_record in enumerate(emails_to_resync):
            self.stdout.write(f"\nProcessing email {i + 1}/{total_emails} (DB ID: {email_record.pk}, Gmail ID: {email_record.message_id})...")

            try:
                # 1. Fetch the correct message from the server
                raw_message_data = dao.get_raw_message(email_record.message_id)
                if not raw_message_data:
                    self.stdout.write(self.style.WARNING("  - SKIPPED: Could not fetch message from Gmail API."))
                    failed_count += 1
                    continue

                # 2. Use the EmailHelper to generate the NEW, unique filename
                email_helper = EmailHelper(raw_message_data, dao, source="gmail")
                
                # --- This is the key part of the new logic ---
                # We will manually construct a new, guaranteed-unique filename
                # by appending the Gmail message ID.
                original_path = email_helper.save_eml(base_download_dir="DL") # Get the standard path
                if not original_path:
                     self.stdout.write(self.style.WARNING("  - SKIPPED: Could not generate a valid file path."))
                     failed_count += 1
                     continue

                path_parts = os.path.splitext(original_path)
                new_unique_path = f"{path_parts[0]}_{email_record.message_id}{path_parts[1]}"
                # --- End of new logic ---

                # 3. Save the new file to disk
                if not dao.download_raw_eml_file(email_record.message_id, new_unique_path):
                    self.stdout.write(self.style.WARNING(f"  - SKIPPED: Failed to download new .eml file to {new_unique_path}"))
                    failed_count += 1
                    continue
                
                self.stdout.write(self.style.SUCCESS(f"  - SAVED new file to {os.path.basename(new_unique_path)}"))

                # 4. Delete the OLD file, if it exists and is different
                old_file_path = email_record.eml_file_path
                if old_file_path and os.path.exists(old_file_path) and old_file_path != new_unique_path:
                    try:
                        os.remove(old_file_path)
                        self.stdout.write(f"  - DELETED old file: {os.path.basename(old_file_path)}")
                    except OSError as e:
                        self.stdout.write(self.style.WARNING(f"  - WARNING: Could not delete old file {old_file_path}: {e}"))

                # 5. Update the database path
                email_record.eml_file_path = new_unique_path
                email_record.save(update_fields=['eml_file_path'])
                self.stdout.write(self.style.SUCCESS("  - UPDATED database path."))
                success_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  - FAILED with unexpected error: {e}"))
                failed_count += 1

        self.stdout.write(self.style.SUCCESS(f"\nResynchronization complete. {success_count} records successfully synced, {failed_count} failed/skipped."))
