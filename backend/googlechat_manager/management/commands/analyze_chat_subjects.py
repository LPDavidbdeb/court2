import json
from django.core.management.base import BaseCommand
from django.db import transaction
from googlechat_manager.models import ChatMessage, ChatSubject, SubjectGroup
from ai_services.services import get_gemini_text_response


class Command(BaseCommand):
    help = 'Sends unprocessed chat messages to Gemini to cluster them into subjects.'

    def add_arguments(self, parser):
        parser.add_argument('--batch-size', type=int, default=50, help='Number of messages to process in one AI call')
        parser.add_argument('--limit', type=int, default=0,
                            help='Limit the total number of batches to process (0 for all)')

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        limit = options['limit']

        # 1. Get unprocessed messages
        messages = ChatMessage.objects.filter(is_processed_by_ai=False).order_by('timestamp')
        total_messages = messages.count()
        self.stdout.write(f"Found {total_messages} unprocessed messages.")

        if total_messages == 0:
            return

        batches_processed = 0

        while True:
            if limit > 0 and batches_processed >= limit:
                break

            # Fetch batch
            batch_qs = ChatMessage.objects.filter(is_processed_by_ai=False).order_by('timestamp')[:batch_size]
            batch_messages = list(batch_qs)

            if not batch_messages:
                break

            self.stdout.write(f"Processing batch {batches_processed + 1} ({len(batch_messages)} messages)...")

            # --- SMART LOGIC: Fetch existing subjects to maintain consistency ---
            # We get a list of existing titles so Gemini can reuse them instead of creating duplicates
            existing_titles = list(ChatSubject.objects.values_list('title', flat=True).distinct())
            existing_titles_str = ", ".join(f'"{t}"' for t in existing_titles)

            # 2. Prepare Transcript
            transcript_lines = []
            for msg in batch_messages:
                sender_name = msg.sender.name if msg.sender else "Unknown"
                timestamp_str = msg.timestamp.strftime('%Y-%m-%d %H:%M')
                # Include ID for linking later
                line = f"[ID: {msg.id}] [{timestamp_str}] {sender_name}: {msg.text_content}"
                transcript_lines.append(line)

            transcript_text = "\n".join(transcript_lines)

            # 3. Construct Prompt with Memory
            system_prompt = (
                "You are an expert conversation analyst. Identify distinct subjects/topics within this log.\n\n"
                "CONTEXT AWARENESS:\n"
                f"We have already identified these topics in previous logs: [{existing_titles_str}].\n"
                "**CRITICAL RULE**: If a conversation below fits one of these existing topics, you MUST use that EXACT title string. "
                "Only create a new title if the topic is clearly new.\n\n"
                "OUTPUT RULES:\n"
                "1. Return ONLY VALID JSON. No markdown formatting.\n"
                "2. Structure: List of objects.\n"
                "3. JSON Format:\n"
                "[\n"
                "  {\n"
                '    "title": "Exact Title String",\n'
                '    "description": "Summary of this specific segment",\n'
                '    "keywords": ["tag1", "tag2"],\n'
                '    "reasoning": "Why this group belongs to this subject",\n'
                '    "message_ids": [123, 124, 125]\n'
                "  }\n"
                "]"
            )

            # 4. Call Gemini
            try:
                response_text = get_gemini_text_response(transcript_text, system_prompt)

                # Clean up potential markdown
                cleaned_response = response_text.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[7:]
                if cleaned_response.startswith("```"):
                    cleaned_response = cleaned_response[3:]
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-3]

                data = json.loads(cleaned_response)

                # 5. Save Results
                self.save_results(data, batch_messages)
                batches_processed += 1

            except json.JSONDecodeError as e:
                self.stderr.write(self.style.ERROR(f"Failed to parse JSON from AI: {e}"))
                # Optional: print response_text to debug
                break
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error processing batch: {e}"))
                break

        self.stdout.write(self.style.SUCCESS(f"Analysis complete. Processed {batches_processed} batches."))

    def save_results(self, subjects_data, batch_messages):
        with transaction.atomic():
            msg_map = {m.id: m for m in batch_messages}

            for subject_item in subjects_data:
                title = subject_item.get('title', 'Untitled Conversation')

                # Try to find case-insensitive match first to avoid "Renovations" vs "renovations"
                subject = ChatSubject.objects.filter(title__iexact=title).first()

                if not subject:
                    subject = ChatSubject.objects.create(
                        title=title,
                        description=subject_item.get('description', ''),
                        keywords=subject_item.get('keywords', [])
                    )

                # Create the Grouping
                group = SubjectGroup.objects.create(
                    subject=subject,
                    reasoning=subject_item.get('reasoning', '')
                )

                # Link messages
                message_ids = subject_item.get('message_ids', [])
                msgs_to_add = []
                for mid in message_ids:
                    if mid in msg_map:
                        msgs_to_add.append(msg_map[mid])

                if msgs_to_add:
                    group.messages.set(msgs_to_add)
                    sorted_msgs = sorted(msgs_to_add, key=lambda x: x.timestamp)
                    group.start_date = sorted_msgs[0].timestamp
                    group.end_date = sorted_msgs[-1].timestamp
                    group.save()

            # Mark processed
            for msg in batch_messages:
                msg.is_processed_by_ai = True
                msg.save(update_fields=['is_processed_by_ai'])