from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View, ListView, DeleteView, UpdateView, DetailView
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.contrib import messages

from ..models import Email, Quote
from ..forms import QuoteForm


class QuoteDetailView(DetailView):
    """
    Displays the details of a single email quote.
    """
    model = Quote
    template_name = 'email_manager/quote_detail.html'
    context_object_name = 'quote'


class QuoteListView(ListView):
    """
    Displays a list of all Emails that have Quotes, ordered by the email's sent date.
    The quotes are grouped by their source email.
    """
    model = Email
    template_name = 'email_manager/quote/list.html'
    context_object_name = 'emails_with_quotes'

    def get_queryset(self):
        """
        Returns a queryset of emails that have at least one quote, ordered by date,
        with quotes prefetched for efficiency.
        """
        return Email.objects.filter(quotes__isnull=False).distinct().order_by('-date_sent').prefetch_related('quotes__trames_narratives')


class QuoteUpdateView(UpdateView):
    """
    Handles updating the narrative associations for a single Quote.
    """
    model = Quote
    form_class = QuoteForm
    template_name = 'email_manager/quote/update.html'
    success_url = reverse_lazy('email_manager:quote_list')

    def get_initial(self):
        """Pre-select the narratives currently associated with the quote."""
        initial = super().get_initial()
        # The reverse relationship from Quote to TrameNarrative is 'trames_narratives'
        initial['trames_narratives'] = self.object.trames_narratives.all()
        return initial

    def get_form(self, form_class=None):
        """Make the quote_text field readonly to focus on narrative association."""
        form = super().get_form(form_class)
        form.fields['quote_text'].widget.attrs['readonly'] = True
        return form

    def form_valid(self, form):
        """Manually save the ManyToMany relationship."""
        self.object = form.save()
        # Get the selected narratives from the form and set them
        self.object.trames_narratives.set(form.cleaned_data['trames_narratives'])
        messages.success(self.request, "The quote's narrative associations have been updated successfully.")
        return super().form_valid(form)


class QuoteDeleteView(DeleteView):
    """
    Handles the deletion of a single Quote object.
    """
    model = Quote
    success_url = reverse_lazy('email_manager:quote_list')

    def form_valid(self, form):
        messages.success(self.request, "The quote has been deleted successfully.")
        return super().form_valid(form)

    def get(self, request, *args, **kwargs):
        """Override get to redirect to post for immediate deletion."""
        return self.post(request, *args, **kwargs)


class AddQuoteView(View):
    """
    Handles adding a quote from an email. This view can handle both standard
    form submissions and AJAX requests from a modal.
    """
    form_class = QuoteForm
    template_name = 'email_manager/quote/partials/add_quote_form.html'

    def get(self, request, *args, **kwargs):
        """
        For AJAX requests, returns the form HTML to be loaded into a modal.
        """
        email = get_object_or_404(Email, pk=kwargs.get('email_pk'))
        form = self.form_class()
        return render(request, self.template_name, {'form': form, 'email': email})

    def post(self, request, *args, **kwargs):
        """
        Handles both AJAX and standard form submissions for creating a quote.
        """
        email = get_object_or_404(Email, pk=kwargs.get('email_pk'))
        form = self.form_class(request.POST)

        if form.is_valid():
            quote = form.save(commit=False)
            quote.email = email
            quote.save()
            form.save_m2m()  # Save the many-to-many relationships

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success', 'message': 'Quote saved successfully!'})
            else:
                messages.success(request, 'Quote saved successfully!')
                return redirect('email_manager:email_detail', pk=email.pk)
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'errors': form.errors.as_json()}, status=400)
        else:
            # For standard submissions, re-render the page with the errors
            messages.error(request, 'Please correct the errors below.')
            # We need a full template for this, not just a partial
            # This part of the logic might need to be adjusted depending on where the standard form is.
            # For now, redirecting back to the email detail page.
            return redirect('email_manager:email_detail', pk=email.pk)
