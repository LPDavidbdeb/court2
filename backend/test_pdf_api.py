import os
import django
import sys
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from pdf_manager.models import PDFDocument
from pdf_manager.schemas import PDFDocumentSchema
from pdf_manager.api import _pdf_to_dict
from pydantic import ValidationError

try:
    qs = PDFDocument.objects.select_related("author", "document_type").prefetch_related("quotes").all()
    print(f"Found {qs.count()} PDFDocuments.")
    
    for p in qs:
        print(f"\n--- Testing document: {p.title} (ID: {p.id}) ---")
        data = _pdf_to_dict(p)
        print("Dictionary materialized successfully.")
        
        try:
            # Ninja uses the schema to validate the returned dict
            schema_obj = PDFDocumentSchema.model_validate(data)
            print("Validation successful!")
        except ValidationError as ve:
            print(f"Validation Error for ID {p.id}:")
            print(ve)
            # Stop at the first error to debug
            break
        
except Exception as e:
    import traceback
    traceback.print_exc()
