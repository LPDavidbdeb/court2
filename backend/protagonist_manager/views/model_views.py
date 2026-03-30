from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.db import transaction
from django.views import View
from django.db.models import Count, Q

from ..models import Protagonist, ProtagonistEmail
from ..forms.protagonist_form import ProtagonistForm, ProtagonistEmailForm

# Import related models
from photos.models import PhotoDocument
from pdf_manager.models import PDFDocument, Quote as PDFQuote
from email_manager.models import Quote as EmailQuote, Email
from document_manager.models import Document
from case_manager.models import LegalCase, ProducedExhibit
from case_manager.services import rebuild_produced_exhibits


# --- List View ---
class ProtagonistListView(ListView):
    model = Protagonist
    template_name = 'protagonist_manager/protagonist_list.html'
    context_object_name = 'protagonists'
    paginate_by = 100
    ordering = ['last_name', 'first_name']


# --- Detail View ---
class ProtagonistDetailView(DetailView):
    model = Protagonist
    template_name = 'protagonist_manager/protagonist_detail.html'
    context_object_name = 'protagonist'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        protagonist = self.get_object()

        context['merge_candidates'] = Protagonist.objects.exclude(pk=self.object.pk).order_by('last_name', 'first_name')
        
        # Check for optional case_id parameter
        case_id = self.request.GET.get('case_id')
        context['case_id'] = case_id
        
        if case_id:
            try:
                case = LegalCase.objects.get(pk=case_id)
                context['case'] = case
                
                # Ensure exhibits are up to date
                if not case.produced_exhibits.exists():
                    rebuild_produced_exhibits(case.pk)
                
                # Filter exhibits related to this protagonist
                related_exhibits = []
                for exhibit in case.produced_exhibits.all():
                    obj = exhibit.content_object
                    if not obj:
                        continue
                        
                    model_name = exhibit.content_type.model
                    is_related = False
                    
                    if model_name == 'email':
                        if obj.sender_protagonist == protagonist:
                            is_related = True
                        elif protagonist in obj.recipient_protagonists.all():
                            is_related = True
                    elif model_name == 'pdfdocument':
                        if obj.author == protagonist:
                            is_related = True
                    elif model_name == 'document':
                        if obj.author == protagonist:
                            is_related = True
                    elif model_name == 'photodocument':
                        if obj.author == protagonist:
                            is_related = True
                    elif model_name == 'chatsequence':
                        # Check messages for this protagonist
                        if obj.messages.filter(sender__protagonist=protagonist).exists():
                            is_related = True
                    
                    if is_related:
                        related_exhibits.append(exhibit)
                
                context['case_exhibits'] = related_exhibits
                
            except LegalCase.DoesNotExist:
                pass

        # Default context data (global view)
        context['photo_documents'] = PhotoDocument.objects.filter(author=protagonist).order_by('-created_at')
        context['pdf_quotes'] = PDFQuote.objects.filter(pdf_document__author=protagonist).order_by('-pdf_document__document_date')
        context['email_quotes'] = EmailQuote.objects.filter(email__thread__protagonist=protagonist).order_by('-email__date_sent')

        return context


# --- Create View ---
class ProtagonistCreateView(CreateView):
    model = Protagonist
    form_class = ProtagonistForm
    template_name = 'protagonist_manager/protagonist_form.html'
    success_url = reverse_lazy('protagonist_manager:protagonist_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Protagonist '{self.object.get_full_name()}' created successfully!")
        return response


# --- Update View ---
class ProtagonistUpdateView(UpdateView):
    model = Protagonist
    form_class = ProtagonistForm
    template_name = 'protagonist_manager/protagonist_form.html'
    context_object_name = 'protagonist'

    def get_success_url(self):
        messages.success(self.request, f"Protagonist '{self.object.get_full_name()}' updated successfully!")
        return reverse_lazy('protagonist_manager:protagonist_detail', kwargs={'pk': self.object.pk})


# --- Delete View ---
class ProtagonistDeleteView(DeleteView):
    model = Protagonist
    template_name = 'protagonist_manager/protagonist_confirm_delete.html'
    success_url = reverse_lazy('protagonist_manager:protagonist_list')
    context_object_name = 'protagonist'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Protagonist '{self.object.get_full_name()}' deleted successfully!")
        return response

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        try:
            self.object.delete()
            messages.success(self.request, f"Protagonist '{self.object.get_full_name()}' deleted successfully.")
            return HttpResponseRedirect(success_url)
        except Exception as e:
            messages.error(self.request, f"Error deleting protagonist '{self.object.get_full_name()}': {e}")
            return HttpResponseRedirect(self.object.get_absolute_url())


# --- Protagonist Email Management Views ---

class ProtagonistEmailCreateView(CreateView):
    model = ProtagonistEmail
    form_class = ProtagonistEmailForm
    template_name = 'protagonist_manager/protagonist_email_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.protagonist = get_object_or_404(Protagonist, pk=self.kwargs['protagonist_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['protagonist'] = self.protagonist
        return context

    def form_valid(self, form):
        form.instance.protagonist = self.protagonist
        response = super().form_valid(form)
        messages.success(self.request,
                         f"Email '{self.object.email_address}' added to {self.protagonist.get_full_name()}.")
        return response

    def get_success_url(self):
        return reverse_lazy('protagonist_manager:protagonist_detail', kwargs={'pk': self.protagonist.pk})


class ProtagonistEmailUpdateView(UpdateView):
    model = ProtagonistEmail
    form_class = ProtagonistEmailForm
    template_name = 'protagonist_manager/protagonist_email_form.html'
    context_object_name = 'email'

    def get_success_url(self):
        return reverse_lazy('protagonist_manager:protagonist_detail', kwargs={'pk': self.object.protagonist.pk})


class ProtagonistEmailDeleteView(DeleteView):
    model = ProtagonistEmail
    template_name = 'protagonist_manager/protagonist_email_confirm_delete.html'
    context_object_name = 'protagonist_email'

    def get_success_url(self):
        return reverse_lazy('protagonist_manager:protagonist_detail', kwargs={'pk': self.object.protagonist.pk})


class MergeProtagonistView(View):
    def post(self, request, *args, **kwargs):
        original_pk = request.POST.get('original_protagonist')
        duplicate_pk = request.POST.get('duplicate_protagonist')

        if not original_pk or not duplicate_pk:
            messages.error(request, "You must select a protagonist to merge.")
            return redirect('protagonist_manager:protagonist_list')

        original = get_object_or_404(Protagonist, pk=original_pk)
        duplicate = get_object_or_404(Protagonist, pk=duplicate_pk)

        try:
            with transaction.atomic():
                Document.objects.filter(author=duplicate).update(author=original)
                Email.objects.filter(sender_protagonist=duplicate).update(sender_protagonist=original)
                for email in Email.objects.filter(recipient_protagonists=duplicate):
                    email.recipient_protagonists.add(original)
                    email.recipient_protagonists.remove(duplicate)
                duplicate.emails.all().update(protagonist=original)
                PDFDocument.objects.filter(author=duplicate).update(author=original)
                PhotoDocument.objects.filter(author=duplicate).update(author=original)
                duplicate.delete()
                messages.success(request, f"Successfully merged '{duplicate.get_full_name()}' into '{original.get_full_name()}'.")
        except Exception as e:
            messages.error(request, f"An error occurred during the merge: {e}")

        return redirect('protagonist_manager:protagonist_detail', pk=original.pk)
