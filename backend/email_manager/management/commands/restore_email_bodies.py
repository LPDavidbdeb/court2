import os
import email
from email.policy import default
from django.core.management.base import BaseCommand
from email_manager.models import Email

def get_email_body(msg):
    """Extracts the plain text body from an email.message.Message object."""
    if msg.is_multipart():
        # For multipart messages, find the first plain text part
        for part in msg.walk():
            if part.get_content_type() == 'text/plain' and part.get('Content-Disposition') is None:
                return part.get_payload(decode=True).decode(part.get_content_charset('utf-8'), errors='ignore')
    else:
        # For single part messages, if it's plain text
        if msg.get_content_type() == 'text/plain':
            return msg.get_payload(decode=True).decode(msg.get_content_charset('utf-8'), errors='ignore')
    return None # Fallback if no plain text body is found

class Command(BaseCommand):
    help = 'Restores the body_plain_text of all Email objects from their original .eml files.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting restoration of email bodies..."))

        emails_to_process = Email.objects.all()
        total_emails = emails_to_process.count()
        updated_count = 0
        failed_count = 0

        for i, email_record in enumerate(emails_to_process):
            self.stdout.write(f"Processing email {i + 1}/{total_emails} (ID: {email_record.pk})...", ending='')

            if not email_record.eml_file_path or not os.path.exists(email_record.eml_file_path):
                self.stdout.write(self.style.WARNING(f" SKIPPED: .eml file not found at {email_record.eml_file_path}"))
                failed_count += 1
                continue

            try:
                with open(email_record.eml_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    msg = email.message_from_file(f, policy=default)
                
                original_body = get_email_body(msg)

                if original_body is None:
                    self.stdout.write(self.style.WARNING(" SKIPPED: No plain text body found in .eml file."))
                    failed_count += 1
                    continue

                # Check if an update is actually needed
                if email_record.body_plain_text != original_body:
                    email_record.body_plain_text = original_body
                    email_record.save(update_fields=['body_plain_text'])
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(" UPDATED"))
                else:
                    self.stdout.write(" OK (no change needed)")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f" FAILED: {e}"))
                failed_count += 1

        self.stdout.write(self.style.SUCCESS(f"\nRestoration complete. {updated_count} records updated, {failed_count} skipped/failed."))
