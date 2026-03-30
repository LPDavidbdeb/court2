import os
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from photos.services import PhotoProcessingService
from photos.models import Photo

class Command(BaseCommand):
    help = 'Performs a clean install: Deletes all existing photos and imports from a source directory, including from date-named subdirectories.'

    def add_arguments(self, parser):
        parser.add_argument('source_directory', type=str, help='The source directory of photos to import.')

    @transaction.atomic
    def handle(self, *args, **options):
        source_directory = options['source_directory']
        if not os.path.isdir(source_directory):
            raise CommandError(f'Source directory "{source_directory}" does not exist.')

        self.stdout.write(self.style.WARNING('--- Starting Clean Install ---'))

        # 1. Delete existing files and objects
        self.stdout.write('Deleting existing photo files and database records...')
        for photo in Photo.objects.all():
            if photo.file and os.path.exists(photo.file.path):
                os.remove(photo.file.path)
        Photo.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Successfully deleted all existing photos.'))

        # 2. Crawl and import new photos
        self.stdout.write(f'Crawling and importing photos from {source_directory}...')
        service = PhotoProcessingService()
        processed_count = 0
        skipped_count = 0

        for item_name in sorted(os.listdir(source_directory)):
            item_path = os.path.join(source_directory, item_name)

            # Case 1: Item is a file
            if os.path.isfile(item_path):
                if item_name.lower().endswith(service.supported_extensions):
                    photo = service.process_photo_file(item_path)
                    if photo:
                        processed_count += 1
                        self.stdout.write(f"  - Imported file: {item_name}")
                    else:
                        skipped_count += 1

            # Case 2: Item is a directory
            elif os.path.isdir(item_path):
                try:
                    date_from_folder = datetime.strptime(item_name, '%Y-%m-%d').date()
                    self.stdout.write(self.style.SUCCESS(f'  - Processing date-named directory: {item_name}'))
                except ValueError:
                    self.stdout.write(self.style.WARNING(f'  - Skipping directory with non-date name: {item_name}'))
                    continue

                for file_name in sorted(os.listdir(item_path)):
                    if not file_name.lower().endswith(service.supported_extensions):
                        continue
                    
                    file_path = os.path.join(item_path, file_name)
                    photo = service.process_photo_file(file_path, date_from_folder=date_from_folder)
                    if photo:
                        processed_count += 1
                        self.stdout.write(f"    - Imported file: {file_name}")
                    else:
                        skipped_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'\n--- Clean Install Complete ---'))
        self.stdout.write(f'Imported {processed_count} new photos.')
        self.stdout.write(f'{skipped_count} photos were skipped (no date found).')
