from pgvector.django import CosineDistance
from email_manager.models import Email
from pdf_manager.models import PDFDocument
from photos.models import PhotoDocument
from document_manager.models import Document
from events.models import Event
from ai_services.services import generate_embedding

def global_semantic_search(query_text, limit=10):
    """
    Searches across all primary evidence sources using vector embeddings.
    Returns a sorted list of dictionaries containing the result type, object, and distance.
    """
    query_vector = generate_embedding(query_text)
    if not query_vector:
        return []

    results = []

    # 1. Emails
    emails = Email.objects.annotate(
        distance=CosineDistance('embedding', query_vector)
    ).filter(embedding__isnull=False).order_by('distance')[:limit]
    for obj in emails:
        results.append({
            'type': 'Email',
            'icon': 'bi-envelope',
            'title': obj.subject or "[Sans sujet]",
            'content': obj.body_plain_text,
            'date': obj.date_sent,
            'distance': obj.distance,
            'url': obj.get_absolute_url()
        })

    # 2. PDF Documents
    pdfs = PDFDocument.objects.annotate(
        distance=CosineDistance('embedding', query_vector)
    ).filter(embedding__isnull=False).order_by('distance')[:limit]
    for obj in pdfs:
        results.append({
            'type': 'PDF',
            'icon': 'bi-file-pdf',
            'title': obj.title,
            'content': obj.ai_analysis,
            'date': obj.document_date,
            'distance': obj.distance,
            'url': obj.get_absolute_url()
        })

    # 3. Events
    events = Event.objects.annotate(
        distance=CosineDistance('embedding', query_vector)
    ).filter(embedding__isnull=False).order_by('distance')[:limit]
    for obj in events:
        results.append({
            'type': 'Événement',
            'icon': 'bi-calendar-event',
            'title': f"Fait du {obj.date}",
            'content': obj.explanation,
            'date': obj.date,
            'distance': obj.distance,
            'url': f"/events/{obj.pk}/"  # Fallback if no absolute_url
        })

    # 4. Photos
    photos = PhotoDocument.objects.annotate(
        distance=CosineDistance('embedding', query_vector)
    ).filter(embedding__isnull=False).order_by('distance')[:limit]
    for obj in photos:
        results.append({
            'type': 'Photo',
            'icon': 'bi-camera',
            'title': obj.title,
            'content': obj.ai_analysis or obj.description,
            'date': obj.created_at,
            'distance': obj.distance,
            'url': f"/photos/documents/{obj.pk}/"
        })

    # 5. Library Documents
    docs = Document.objects.annotate(
        distance=CosineDistance('embedding', query_vector)
    ).filter(embedding__isnull=False).order_by('distance')[:limit]
    for obj in docs:
        results.append({
            'type': 'Document',
            'icon': 'bi-file-earmark-text',
            'title': obj.title,
            'content': obj.solemn_declaration,
            'date': obj.document_original_date,
            'distance': obj.distance,
            'url': obj.get_absolute_url()
        })

    # Sort all results by distance (closest first)
    results.sort(key=lambda x: x['distance'])

    return results[:limit]
