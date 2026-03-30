from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.paginator import Paginator
from .models import ChatMessage, ChatSequence
from .forms import ChatSequenceForm
import json

def single_chat_stream(request):
    """
    Renders the main chat stream, now handling both creation and editing.
    """
    edit_sequence_id = request.GET.get('edit')
    editing_sequence = None
    preselected_ids = []

    if edit_sequence_id:
        editing_sequence = get_object_or_404(ChatSequence, pk=edit_sequence_id)
        # Convert IDs to strings to ensure correct matching in JavaScript
        preselected_ids = [str(id) for id in editing_sequence.messages.values_list('id', flat=True)]

    all_messages = ChatMessage.objects.select_related('sender').order_by('timestamp')
    paginator = Paginator(all_messages, 50)
    last_page_num = paginator.num_pages
    page_obj = paginator.page(last_page_num)
    
    context = {
        'chat_messages': page_obj.object_list,
        'page_number': last_page_num,
        'has_previous': page_obj.has_previous(),
        'is_detail_view': False,
        'editing_sequence': editing_sequence,
        'preselected_ids_json': json.dumps(preselected_ids),
    }
    return render(request, 'googlechat_manager/chat_stream.html', context)

def load_more_messages(request):
    page_number = int(request.GET.get('page', 1))
    all_messages = ChatMessage.objects.select_related('sender').order_by('timestamp')
    paginator = Paginator(all_messages, 50)
    
    if page_number < 1 or page_number > paginator.num_pages:
        return JsonResponse({'messages': [], 'has_previous': False})
        
    page_obj = paginator.page(page_number)
    messages_data = [{'id': msg.id, 'sender_name': msg.sender.name if msg.sender else "Unknown", 'text_content': msg.text_content, 'timestamp': msg.timestamp.strftime('%b %d, %Y, %I:%M %p')} for msg in page_obj.object_list]
    return JsonResponse({'messages': messages_data, 'has_previous': page_obj.has_previous()})

def chat_sequence_list(request):
    sequences = ChatSequence.objects.prefetch_related('messages').order_by('-created_at')
    return render(request, 'googlechat_manager/sequence_list.html', {'sequences': sequences})

def chat_sequence_detail(request, pk):
    sequence = get_object_or_404(ChatSequence.objects.prefetch_related('messages__sender'), pk=pk)
    context = {'chat_messages': sequence.messages.all(), 'sequence_title': sequence.title, 'is_detail_view': True}
    return render(request, 'googlechat_manager/chat_stream.html', context)

@require_POST
def create_sequence_ajax(request):
    data = json.loads(request.body)
    message_ids = data.get('message_ids', [])
    title = data.get('title')
    if not title or not message_ids:
        return JsonResponse({'status': 'error', 'message': 'Missing data'}, status=400)
    sequence = ChatSequence.objects.create(title=title)
    msgs = ChatMessage.objects.filter(id__in=message_ids)
    sequence.messages.set(msgs)
    sequence.update_dates()
    return JsonResponse({'status': 'success', 'redirect_url': '/chat/sequences/'})

@require_POST
def update_sequence_ajax(request, pk):
    """Handles updating an existing sequence."""
    data = json.loads(request.body)
    message_ids = data.get('message_ids', [])
    title = data.get('title')
    if not title or not message_ids:
        return JsonResponse({'status': 'error', 'message': 'Missing data'}, status=400)
    
    sequence = get_object_or_404(ChatSequence, pk=pk)
    sequence.title = title
    sequence.save(update_fields=['title'])
    
    msgs = ChatMessage.objects.filter(id__in=message_ids)
    sequence.messages.set(msgs)
    sequence.update_dates()
    
    return JsonResponse({'status': 'success', 'redirect_url': '/chat/sequences/'})

@require_POST
def delete_sequence(request, pk):
    seq = get_object_or_404(ChatSequence, pk=pk)
    seq.delete()
    messages.success(request, "Sequence deleted.")
    return redirect('googlechat:sequence_list')