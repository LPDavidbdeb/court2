from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.db import transaction
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

from .models import Protagonist, ProtagonistEmail
from .forms import ProtagonistForm, ProtagonistEmailForm
from document_manager.models import Document
from email_manager.models import Email
from pdf_manager.models import PDFDocument
from photos.models import PhotoDocument

class ProtagonistListView(ListView):
    model = Protagonist
    template_name = 'protagonist_manager/protagonist_list.html'
    context_object_name = 'protagonists'

class ProtagonistDetailView(DetailView):
    model = Protagonist
    template_name = 'protagonist_manager/protagonist_detail.html'
    context_object_name = 'protagonist'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all other protagonists to be candidates for merging
        context['merge_candidates'] = Protagonist.objects.exclude(pk=self.object.pk)
        return context

class ProtagonistCreateWithEmailsView(CreateView):
    model = Protagonist
    form_class = ProtagonistForm
    template_name = 'protagonist_manager/protagonist_form.html'
    success_url = reverse_lazy('protagonist_manager:protagonist_list')

class ProtagonistUpdateView(UpdateView):
    model = Protagonist
    form_class = ProtagonistForm
    template_name = 'protagonist_manager/protagonist_form.html'
    
    def get_success_url(self):
        return reverse_lazy('protagonist_manager:protagonist_detail', kwargs={'pk': self.object.pk})

class ProtagonistDeleteView(DeleteView):
    model = Protagonist
    template_name = 'protagonist_manager/protagonist_confirm_delete.html'
    success_url = reverse_lazy('protagonist_manager:protagonist_list')

class ProtagonistEmailCreateView(CreateView):
    model = ProtagonistEmail
    form_class = ProtagonistEmailForm
    template_name = 'protagonist_manager/protagonist_email_form.html'

    def form_valid(self, form):
        form.instance.protagonist = get_object_or_404(Protagonist, pk=self.kwargs['protagonist_pk'])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('protagonist_manager:protagonist_detail', kwargs={'pk': self.kwargs['protagonist_pk']})

class ProtagonistEmailUpdateView(UpdateView):
    model = ProtagonistEmail
    form_class = ProtagonistEmailForm
    template_name = 'protagonist_manager/protagonist_email_form.html'

    def get_success_url(self):
        return reverse_lazy('protagonist_manager:protagonist_detail', kwargs={'pk': self.object.protagonist.pk})

class ProtagonistEmailDeleteView(DeleteView):
    model = ProtagonistEmail
    template_name = 'protagonist_manager/protagonist_email_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('protagonist_manager:protagonist_detail', kwargs={'pk': self.object.protagonist.pk})

class MergeProtagonistView(View):
    def post(self, request, *args, **kwargs):
        original_pk = request.POST.get('original_protagonist')
        duplicate_pk = request.POST.get('duplicate_protagonist')

        if not original_pk or not duplicate_pk:
            messages.error(request, "You must select a protagonist to merge.")
            # We don't know which detail page to return to, so we go to the list view
            return redirect('protagonist_manager:protagonist_list')

        original = get_object_or_404(Protagonist, pk=original_pk)
        duplicate = get_object_or_404(Protagonist, pk=duplicate_pk)

        try:
            with transaction.atomic():
                # 1. Re-assign Document authors
                Document.objects.filter(author=duplicate).update(author=original)

                # 2. Re-assign Email senders
                Email.objects.filter(sender_protagonist=duplicate).update(sender_protagonist=original)

                # 3. Re-assign Email recipients (ManyToManyField)
                for email in Email.objects.filter(recipient_protagonists=duplicate):
                    email.recipient_protagonists.add(original)
                    email.recipient_protagonists.remove(duplicate)

                # 4. Re-assign ProtagonistEmail objects
                duplicate.emails.all().update(protagonist=original)

                # 5. Re-assign PDFDocument authors
                PDFDocument.objects.filter(author=duplicate).update(author=original)
                
                # 6. Re-assign PhotoDocument authors
                PhotoDocument.objects.filter(author=duplicate).update(author=original)

                # 7. Delete the duplicate protagonist
                duplicate.delete()

                messages.success(request, f"Successfully merged '{duplicate.get_full_name()}' into '{original.get_full_name()}'.")

        except Exception as e:
            messages.error(request, f"An error occurred during the merge: {e}")

        return redirect('protagonist_manager:protagonist_detail', pk=original.pk)

@require_POST
def update_protagonist_role_ajax(request):
    try:
        data = json.loads(request.body)
        protagonist_id = data.get('protagonist_id')
        new_role = data.get('role')

        protagonist = Protagonist.objects.get(pk=protagonist_id)
        protagonist.role = new_role
        protagonist.save()

        return JsonResponse({'status': 'success'})
    except Protagonist.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Protagonist not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@require_POST
def update_protagonist_linkedin_ajax(request):
    try:
        data = json.loads(request.body)
        protagonist_id = data.get('protagonist_id')
        new_linkedin_url = data.get('linkedin_url')

        protagonist = Protagonist.objects.get(pk=protagonist_id)
        protagonist.linkedin_url = new_linkedin_url
        protagonist.save()

        return JsonResponse({'status': 'success'})
    except Protagonist.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Protagonist not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def search_protagonists_ajax(request):
    term = request.GET.get('term', '')
    protagonists = Protagonist.objects.filter(first_name__icontains=term) | Protagonist.objects.filter(last_name__icontains=term)
    results = [{'id': p.id, 'text': p.get_full_name()} for p in protagonists[:10]]
    return JsonResponse({'results': results})
