from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib import messages
from django.db import transaction

from ..models import Protagonist
from ..forms.protagonist_form import ProtagonistForm
from ..forms.ProtagonistEmailFormSet import ProtagonistEmailFormSet

class ProtagonistCreateWithEmailsView(CreateView):
    model = Protagonist
    form_class = ProtagonistForm
    template_name = 'protagonist_manager/protagonist_create_with_emails.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['email_formset'] = ProtagonistEmailFormSet(self.request.POST, prefix='emails')
        else:
            context['email_formset'] = ProtagonistEmailFormSet(prefix='emails')
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        email_formset = context['email_formset']
        
        with transaction.atomic():
            self.object = form.save()
            if email_formset.is_valid():
                email_formset.instance = self.object
                email_formset.save()
                messages.success(self.request, f"Protagonist '{self.object.get_full_name()}' and associated emails created successfully!")
                return redirect(self.get_success_url())
        
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('protagonist_manager:protagonist_detail', kwargs={'pk': self.object.pk})
