from django.core.management.base import BaseCommand
from django.db import transaction
from email_manager.models import Email
from protagonist_manager.utils import get_or_create_protagonist_from_email_string

class Command(BaseCommand):
    help = 'Backfills the sender_protagonist and recipient_protagonists for existing emails.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting backfill process for email protagonists..."))

        emails_to_process = Email.objects.all()
        total_emails = emails_to_process.count()
        self.stdout.write(f"Found {total_emails} emails to process.")

        updated_count = 0

        with transaction.atomic():
            for i, email in enumerate(emails_to_process):
                if (i + 1) % 100 == 0:
                    self.stdout.write(f"Processing email {i + 1}/{total_emails}...")

                # --- Process Sender ---
                if email.sender and not email.sender_protagonist:
                    sender_protagonist = get_or_create_protagonist_from_email_string(email.sender)
                    if sender_protagonist:
                        email.sender_protagonist = sender_protagonist
                        email.save(update_fields=['sender_protagonist'])
                        updated_count += 1

                # --- Process Recipients ---
                all_recipient_protagonists = list(email.recipient_protagonists.all())
                existing_recipient_ids = {p.id for p in all_recipient_protagonists}
                needs_update = False

                recipient_fields = [email.recipients_to, email.recipients_cc, email.recipients_bcc]
                for field in recipient_fields:
                    if not field:
                        continue
                    
                    # Split string by comma for multiple recipients
                    for single_email_str in field.split(','):
                        protagonist = get_or_create_protagonist_from_email_string(single_email_str.strip())
                        if protagonist and protagonist.id not in existing_recipient_ids:
                            all_recipient_protagonists.append(protagonist)
                            existing_recipient_ids.add(protagonist.id)
                            needs_update = True

                if needs_update:
                    email.recipient_protagonists.set(all_recipient_protagonists)
                    if not email.sender_protagonist: # Avoid double counting if sender was also updated
                        updated_count +=1

        self.stdout.write(self.style.SUCCESS(f"\nBackfill complete. Updated information for {updated_count} emails."))
