import os
import django
import sys
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.test import Client
from django.conf import settings

def test_headers():
    client = Client()
    # We test a path that should be handled by Django and have the middleware applied.
    # The /api/status/ or any other valid path.
    response = client.get('/api/status/')
    print(f"Path: /api/status/")
    print(f"Status: {response.status_code}")
    print(f"X-Frame-Options: {response.get('X-Frame-Options')}")
    
    if response.get('X-Frame-Options') == 'SAMEORIGIN':
        print("\nSUCCESS: X-Frame-Options is correctly set to 'SAMEORIGIN'.")
    else:
        print(f"\nFAILURE: Expected 'SAMEORIGIN', got '{response.get('X-Frame-Options')}'")

if __name__ == "__main__":
    test_headers()
