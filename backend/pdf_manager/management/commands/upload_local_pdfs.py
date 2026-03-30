import os
from django.core.management.base import BaseCommand
from django.core.files import File
from django.core.files.storage import default_storage
from django.conf import settings
from pdf_manager.models import PDFDocument


class Command(BaseCommand):
    help = 'Uploads local PDF files to Google Cloud Storage.'

    def handle(self, *args, **options):
        # 1. Safety Check
        is_google_storage = False
        if hasattr(settings, 'STORAGES'):
            backend = settings.STORAGES.get('default', {}).get('BACKEND', '').lower()
            if 'google' in backend or 'gcloud' in backend:
                is_google_storage = True

        if not is_google_storage:
            self.stdout.write(self.style.ERROR(
                "ERROR: Google Cloud Storage is not active. Run with --settings=mysite.settings.remote"))
            return

        pdfs = PDFDocument.objects.all()
        total = pdfs.count()
        self.stdout.write(f"Checking {total} PDFs...")

        for i, pdf in enumerate(pdfs):
            if not pdf.file:
                continue

            # 1. SMART CHECK: Ask Google if the file is already there
            # This avoids re-uploading and is the standard way to handle this.
            if default_storage.exists(pdf.file.name):
                self.stdout.write(self.style.SUCCESS(f"[{i + 1}/{total}] SKIPPING (Already in Cloud): {pdf.title}"))
                continue

            # 2. UPLOAD: If not in cloud, find it locally and push it
            # --- CORRECTED LINE ---
            # Construct the local path manually to avoid calling the cloud storage 'path' method.
            local_path = os.path.join(settings.MEDIA_ROOT, pdf.file.name)

            if os.path.exists(local_path):
                try:
                    with open(local_path, 'rb') as f:
                        django_file = File(f)
                        # Saving trigger the upload
                        pdf.file.save(os.path.basename(pdf.file.name), django_file, save=True)
                        self.stdout.write(self.style.SUCCESS(f"[{i + 1}/{total}] UPLOADED: {pdf.title}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Failed {pdf.title}: {e}"))
            else:
                self.stdout.write(self.style.WARNING(f"Local file missing: {local_path}"))
