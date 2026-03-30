import os
from django.db.models import Min
from django.shortcuts import redirect, get_object_or_404, render
from django.views.generic import ListView, DetailView, FormView, DeleteView, View
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseRedirect

from ..models import EmailThread, Quote
from ..forms import EmailAjaxSearchForm, QuoteForm
from ..utils import search_gmail, save_gmail_thread


class EmailThreadListView(ListView):
    model = EmailThread
    template_name = 'email_manager/thread/list.html'
    context_object_name = 'threads'

    def get_queryset(self):
        return EmailThread.objects.annotate(
            start_date=Min('emails__date_sent')
        ).order_by('-start_date')


class EmailThreadDetailView(DetailView):
    model = EmailThread
    template_name = 'email_manager/thread/detail.html'
    context_object_name = 'thread'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        thread = self.get_object()
        
        # 1. Get the "Start Date" of the current thread (same metric used in List View)
        # We assume the list is ordered by the date of the FIRST email in the thread
        current_min_date = thread.emails.aggregate(mn=Min('date_sent'))['mn']

        # 2. Find Neighbors
        if current_min_date:
            # PREVIOUS THREAD (Newer than current -> Date is GREATER)
            # We want the 'smallest' date that is still larger than ours (closest neighbor upwards)
            context['previous_thread'] = EmailThread.objects.annotate(
                start_date=Min('emails__date_sent')
            ).filter(
                start_date__gt=current_min_date
            ).order_by('start_date').first()

            # NEXT THREAD (Older than current -> Date is SMALLER)
            # We want the 'largest' date that is smaller than ours (closest neighbor downwards)
            context['next_thread'] = EmailThread.objects.annotate(
                start_date=Min('emails__date_sent')
            ).filter(
                start_date__lt=current_min_date
            ).order_by('-start_date').first()

        context['emails_in_thread'] = thread.emails.all().order_by('date_sent')
        context['form'] = QuoteForm()
        
        # --- NEW: Fetch all quotes for this thread ---
        # We filter quotes where the related email belongs to this thread
        context['thread_quotes'] = Quote.objects.filter(
            email__thread=thread
        ).select_related('email').prefetch_related('trames_narratives').order_by('email__date_sent')

        return context


class EmailSearchView(FormView):
    template_name = 'email_manager/thread/search.html'
    form_class = EmailAjaxSearchForm
    success_url = reverse_lazy('email_manager:thread_list')

    def form_valid(self, form):
        try:
            search_results = search_gmail(form.cleaned_data)
        except Exception as e:
            messages.error(self.request, f"An error occurred during the search: {e}")
            search_results = {'status': 'error', 'message': str(e)}

        context = self.get_context_data(form=form, search_results=search_results)
        
        if search_results.get('status') == 'success':
            context['selected_protagonist'] = search_results.get('selected_protagonist')

        return self.render_to_response(context)


class EmailThreadDeleteView(DeleteView):
    model = EmailThread
    success_url = reverse_lazy('email_manager:thread_list')

    def form_valid(self, form):
        thread = self.get_object()
        thread_subject = thread.subject
        for email_record in thread.emails.all():
            if email_record.eml_file_path and os.path.exists(email_record.eml_file_path):
                try:
                    os.remove(email_record.eml_file_path)
                except OSError as e:
                    messages.warning(self.request, f"Failed to delete EML file {email_record.eml_file_path}: {e}")

        response = super().form_valid(form)
        messages.success(self.request, f"Thread '{thread_subject}' and all its messages deleted successfully.")
        return response

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


class EmailThreadSaveView(View):
    def post(self, request, *args, **kwargs):
        thread_id = request.POST.get('thread_id')
        protagonist_id = request.POST.get('protagonist_id')

        try:
            new_thread = save_gmail_thread(thread_id, protagonist_id)
            messages.success(request, f"Successfully saved thread '{new_thread.subject}'.")
            return redirect('email_manager:thread_detail', pk=new_thread.pk)
        except Exception as e:
            messages.error(request, f"An error occurred while saving the thread: {e}")
            return HttpResponseRedirect(reverse('email_manager:thread_search'))
