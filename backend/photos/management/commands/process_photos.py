import os
import html
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
import exifread

from photos.services import PhotoProcessingService
from photos.models import Photo, PhotoType

class Command(BaseCommand):
    help = 'Processes photos from a source directory with different modes.'

    def add_arguments(self, parser):
        parser.add_argument('source_directory', type=str, help='The source directory of photos.')
        parser.add_argument('--mode', type=str, default='add_by_path', choices=['add_by_path', 'add_by_timestamp', 'add_interactive', 'clean'])
        parser.add_argument('--photo-type-id', type=int, default=None)

    def handle(self, *args, **options):
        for message in self.handle_streaming(**options):
            cleaned_message = message.replace("data: ", "").replace("\n\n", "").strip()
            self.stdout.write(cleaned_message)

    def handle_streaming(self, **options):
        source_directory = options['source_directory']
        mode = options['mode']
        photo_type_id = options['photo_type_id']

        def stream_message(message, level='info'):
            safe_message = html.escape(message)
            return f"data: <p class='log log-{level}'>{safe_message}</p>\n\n"

        def stream_interactive_prompt(file_path, file_name):
            escaped_file_path = html.escape(file_path)
            escaped_file_name = html.escape(file_name)
            prompt_id = f"prompt-{hash(file_path)}"

            prompt_html = f'''
<div id="{prompt_id}" class="log log-interactive-prompt" data-file-path="{escaped_file_path}" data-status="unprocessed">
    <p>File '{escaped_file_name}' is missing a date. Please provide one:</p>
    <div class="input-group">
        <input type="datetime-local" class="form-control manual-date-input">
        <button class="btn btn-primary btn-sm" onclick="submitManualDate(this)">Import</button>
        <button class="btn btn-secondary btn-sm" onclick="document.getElementById('{prompt_id}').setAttribute('data-status', 'processed'); document.getElementById('{prompt_id}').style.display='none';">Skip</button>
    </div>
    <div class="status-message mt-2"></div>
</div>
'''
            prompt_html_minimized = prompt_html.replace('\n', '')
            return f"data: {prompt_html_minimized}\n\n"

        yield stream_message("Process started...")

        photo_type = None
        if photo_type_id:
            try:
                photo_type = PhotoType.objects.get(pk=photo_type_id)
                yield stream_message(f"Assigning Photo Type: {photo_type.name}")
            except PhotoType.DoesNotExist:
                yield stream_message(f"PhotoType with ID {photo_type_id} not found.", 'error')
                return

        service = PhotoProcessingService()
        
        if mode == 'clean':
            yield stream_message("Deleting existing photos...", 'warning')
            Photo.objects.all().delete()
            yield stream_message("Deleted existing photo records.")

        existing_timestamps = set()
        if mode == 'add_by_timestamp':
            yield stream_message("Fetching existing timestamps...")
            existing_timestamps = {dt.replace(second=0, microsecond=0) for dt in Photo.objects.values_list('datetime_original', flat=True) if dt}
            yield stream_message(f"Found {len(existing_timestamps)} unique timestamps (to the minute).")

        yield stream_message(f"Crawling directory: {source_directory}")
        processed_count = 0
        skipped_count = 0

        for root, _, files in os.walk(source_directory):
            for file_name in sorted(files):
                if not file_name.lower().endswith(service.supported_extensions):
                    continue

                file_path = os.path.join(root, file_name)
                
                if Photo.objects.filter(file_path=file_path).exists():
                    yield stream_message(f"SKIPPED: {file_name} - Reason: File path already exists in database.", 'warning')
                    skipped_count += 1
                    continue

                dt = None
                try:
                    with open(file_path, 'rb') as f:
                        tags = exifread.process_file(f, details=False, stop_tag='EXIF DateTimeOriginal')
                    dt = service._parse_date(tags)
                except Exception:
                    pass # Ignore errors, we will handle missing dt below

                if not dt:
                    if mode == 'add_interactive':
                        yield stream_interactive_prompt(file_path, file_name)
                        continue
                    else:
                        yield stream_message(f"SKIPPED: {file_name} - Reason: No valid date found in EXIF data.", 'warning')
                        skipped_count += 1
                        continue

                if mode == 'add_by_timestamp':
                    dt_truncated = dt.replace(second=0, microsecond=0)
                    if dt_truncated in existing_timestamps:
                        yield stream_message(f"SKIPPED: {file_name} - Reason: A photo with the same timestamp already exists.", 'warning')
                        skipped_count += 1
                        continue
                
                photo = service.process_photo_file(file_path, photo_type=photo_type)
                if photo:
                    processed_count += 1
                    yield stream_message(f"IMPORTED: {file_name}", 'success')
                    if mode == 'add_by_timestamp':
                        existing_timestamps.add(photo.datetime_original.replace(second=0, microsecond=0))
                else:
                    yield stream_message(f"SKIPPED: {file_name} - Reason: Processing service failed.", 'error')
                    skipped_count += 1

        yield stream_message(f"\n--- Processing Complete ---", 'success')
        yield stream_message(f"Imported {processed_count} new photos.")
        yield stream_message(f"Skipped {skipped_count} photos.")
