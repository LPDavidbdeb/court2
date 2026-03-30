import json
import os
from dateutil import parser
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from googlechat_manager.models import ChatParticipant, ChatThread, ChatMessage


class Command(BaseCommand):
    help = 'Ingests Google Chat Takeout JSON files into the database.'

    def add_arguments(self, parser):
        parser.add_argument('--message-files', type=str, help='Path to the messages.json file')
        parser.add_argument('--users-file', type=str, help='Path to the group_info.json file (optional)',
                            required=False)

    def handle(self, *args, **options):
        file_path = options['message_files']
        # users_file is available if needed for future expansion

        if not file_path or not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        self.stdout.write(self.style.NOTICE(f"Processing file: {file_path}"))

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            messages = data.get('messages', [])

            if not messages:
                self.stdout.write(self.style.ERROR("Could not find a list of messages to process."))
                return

            self.process_messages(messages)

        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f"Invalid JSON in file: {file_path}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error processing file: {e}"))

    def process_messages(self, messages):
        count = 0
        total = len(messages)

        with transaction.atomic():
            for msg_data in messages:
                # --- 1. Handle Creator/Sender ---
                # Your JSON uses 'creator', standard API uses 'sender'
                creator_data = msg_data.get('creator') or msg_data.get('sender', {})

                # In your JSON, the email is the best unique ID
                sender_id = creator_data.get('email') or creator_data.get('name')

                if not sender_id:
                    # Skip system messages without a sender
                    continue

                # FIXED: Removed 'original_user_id' from defaults as it is not in the model
                # The first argument 'original_id' sets the unique key.
                sender, _ = ChatParticipant.objects.get_or_create(
                    original_id=sender_id,
                    defaults={
                        'name': creator_data.get('name'),
                        'email': creator_data.get('email'),
                    }
                )

                # --- 2. Handle Thread/Topic ---
                # Your JSON uses 'topic_id'
                thread_id = msg_data.get('topic_id')

                # Fallback for standard API format
                if not thread_id and 'thread' in msg_data:
                    thread_id = msg_data['thread'].get('name')

                if not thread_id:
                    # Cannot link message without a thread ID
                    continue

                # Create or retrieve the thread
                chat_thread, _ = ChatThread.objects.get_or_create(
                    original_thread_id=thread_id,
                    defaults={'space_id': None}  # Your export doesn't seem to have Space IDs
                )

                # --- 3. Handle Timestamp ---
                # Your JSON uses 'created_date', standard API uses 'createTime'
                date_str = msg_data.get('created_date') or msg_data.get('createTime')

                if date_str:
                    try:
                        # Dateutil parser handles "Tuesday, September 2, 2014 at 2:10:17 PM UTC"
                        timestamp = parser.parse(date_str)
                        if timezone.is_naive(timestamp):
                            timestamp = timezone.make_aware(timestamp)
                    except (ValueError, TypeError):
                        timestamp = timezone.now()
                else:
                    timestamp = timezone.now()

                # --- 4. Create Message ---
                ChatMessage.objects.update_or_create(
                    timestamp=timestamp,
                    sender=sender,
                    thread=chat_thread,
                    defaults={
                        'text_content': msg_data.get('text', ''),
                        'raw_data': msg_data,
                        'is_processed_by_ai': False
                    }
                )

                count += 1
                if count % 100 == 0:
                    self.stdout.write(f"Processed {count}/{total} messages...")

        self.stdout.write(self.style.SUCCESS(f"Successfully ingested {count} messages."))