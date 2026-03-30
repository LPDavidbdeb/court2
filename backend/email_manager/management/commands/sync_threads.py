from django.core.management.base import BaseCommand, CommandError
from email_manager.models import Email, EmailThread
from DAL.gmailDAO import GmailDAO
from helpers.Email import Email as EmailHelper
from dateutil import parser

# Import the new utility function
from protagonist_manager.utils import get_or_create_protagonist_from_email_string

class Command(BaseCommand):
    help = 'Syncs saved email threads with Gmail to fetch any missing messages.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--thread_pk',
            type=int,
            help='Specify the database PK of a single EmailThread to sync.',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting email thread synchronization..."))

        thread_pk = options['thread_pk']
        threads_to_sync = []

        if thread_pk:
            try:
                thread = EmailThread.objects.get(pk=thread_pk)
                if not thread.emails.filter(dao_source='gmail').exists():
                    raise CommandError(f"Thread PK {thread_pk} is not a Gmail thread and cannot be synced.")
                threads_to_sync.append(thread)
                self.stdout.write(f"Targeting single thread: '{thread.subject}' (PK: {thread.pk})")
            except EmailThread.DoesNotExist:
                raise CommandError(f"EmailThread with PK {thread_pk} does not exist.")
        else:
            threads_to_sync = EmailThread.objects.filter(emails__dao_source='gmail').distinct()
            self.stdout.write(f"Found {threads_to_sync.count()} Gmail threads to sync.")

        if not threads_to_sync.count():
            self.stdout.write(self.style.WARNING("No Gmail threads found to sync."))
            return

        dao = GmailDAO()
        if not dao.connect():
            raise CommandError("Could not connect to Gmail API. Please check credentials.")

        total_synced_count = 0

        for thread in threads_to_sync:
            self.stdout.write(f"---\nChecking thread: '{thread.subject}' (Thread ID: {thread.thread_id})")

            try:
                remote_message_ids = {msg['id'] for msg in dao.get_raw_thread_messages(thread.thread_id)}
                local_message_ids = set(thread.emails.values_list('message_id', flat=True))
                missing_ids = remote_message_ids - local_message_ids

                if not missing_ids:
                    self.stdout.write(self.style.SUCCESS("Thread is already up to date."))
                    continue

                self.stdout.write(self.style.WARNING(f"Found {len(missing_ids)} missing messages. Fetching them now..."))

                for msg_id in missing_ids:
                    raw_message = dao.get_raw_message(msg_id)
                    if not raw_message:
                        self.stderr.write(self.style.ERROR(f"Could not fetch message ID {msg_id}. Skipping."))
                        continue

                    email_helper = EmailHelper(raw_message_data=raw_message, dao_instance=dao, source='gmail')
                    eml_path = email_helper.save_eml()
                    date_sent_str = email_helper.headers.get('Date')
                    date_sent_dt = parser.parse(date_sent_str) if date_sent_str else None

                    # --- New Protagonist Logic ---
                    sender_str = email_helper.headers.get('From')
                    sender_protagonist = get_or_create_protagonist_from_email_string(sender_str)

                    recipient_protagonists = []
                    for recipient_field in ['To', 'Cc', 'Bcc']:
                        recipient_str = email_helper.headers.get(recipient_field)
                        if recipient_str:
                            # Split string by comma for multiple recipients
                            for single_email_str in recipient_str.split(','):
                                protagonist = get_or_create_protagonist_from_email_string(single_email_str)
                                if protagonist:
                                    recipient_protagonists.append(protagonist)
                    # --- End New Logic ---

                    new_email = Email.objects.create(
                        thread=thread,
                        message_id=email_helper.id,
                        dao_source='gmail',
                        subject=email_helper.headers.get('Subject'),
                        sender=sender_str, # Keep the raw string for reference
                        recipients_to=email_helper.headers.get('To'),
                        recipients_cc=email_helper.headers.get('Cc'),
                        recipients_bcc=email_helper.headers.get('Bcc'),
                        date_sent=date_sent_dt,
                        body_plain_text=email_helper.body_plain_text,
                        eml_file_path=eml_path,
                        sender_protagonist=sender_protagonist, # Set the new field
                    )

                    # Set the many-to-many relationship for recipients
                    if recipient_protagonists:
                        new_email.recipient_protagonists.set(list(set(recipient_protagonists))) # Use set to ensure uniqueness

                    self.stdout.write(f"  - Saved new message: '{email_helper.headers.get('Subject')}'")
                    total_synced_count += 1

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"An error occurred while syncing thread {thread.thread_id}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"\nSynchronization complete. Fetched {total_synced_count} new messages in total."))
