from django.core.management.base import BaseCommand
from case_manager.models import AISuggestion
import json

def _normalize_suggestion_json(data_dict):
    """
    Normalizes the AI suggestion JSON to a standard format.
    """
    normalized_data = {}
    
    # Find keys that seem to correspond to the four sections
    keys = list(data_dict.keys())
    
    # A common pattern is having 'suggestion_secX' and 'contenu_secX'
    # We prioritize 'contenu' if it exists
    for i in range(1, 5):
        title_key = f'suggestion_sec{i}'
        content_key = f'contenu_sec{i}'
        
        # Find the best key for the content
        content = data_dict.get(content_key, data_dict.get(title_key, ''))
        
        normalized_data[f'section_{i}'] = content

    return normalized_data

class Command(BaseCommand):
    help = 'Normalizes the JSON content of all AISuggestion objects.'

    def handle(self, *args, **options):
        suggestions = AISuggestion.objects.all()
        count = 0
        for suggestion in suggestions:
            if suggestion.parsing_success and isinstance(suggestion.content, dict):
                original_content = suggestion.content
                normalized_content = _normalize_suggestion_json(original_content)
                
                # Check if the content actually changed to avoid unnecessary writes
                if original_content != normalized_content:
                    suggestion.content = normalized_content
                    suggestion.save()
                    count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Successfully normalized {count} AI suggestions.'))
