from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django import forms
from .models import TrameNarrative, PerjuryArgument

class TrameNarrativeAdminForm(forms.ModelForm):
    class Meta:
        model = TrameNarrative
        fields = '__all__'
        widgets = {
            'citations_chat': FilteredSelectMultiple(
                verbose_name='Chat Sequences',
                is_stacked=False
            ),
            'citations_courriel': FilteredSelectMultiple(
                verbose_name='Email Quotes',
                is_stacked=False
            ),
            'citations_pdf': FilteredSelectMultiple(
                verbose_name='PDF Quotes',
                is_stacked=False
            ),
            'photo_documents': FilteredSelectMultiple(
                verbose_name='Photo Documents',
                is_stacked=False
            ),
            'evenements': FilteredSelectMultiple(
                verbose_name='Events',
                is_stacked=False
            ),
            'targeted_statements': FilteredSelectMultiple(
                verbose_name='Targeted Statements',
                is_stacked=False
            ),
            'source_statements': FilteredSelectMultiple(
                verbose_name='Source Statements',
                is_stacked=False
            ),
        }

class PerjuryArgumentInline(admin.StackedInline):
    model = PerjuryArgument
    can_delete = False
    verbose_name_plural = 'Perjury Argument Details'

@admin.register(TrameNarrative)
class TrameNarrativeAdmin(admin.ModelAdmin):
    form = TrameNarrativeAdminForm
    inlines = (PerjuryArgumentInline,)
    list_display = ('titre', 'type_argument', 'resume')
    search_fields = ('titre', 'resume')
    filter_horizontal = (
        'citations_chat', 
        'citations_courriel', 
        'citations_pdf', 
        'photo_documents', 
        'evenements', 
        'targeted_statements', 
        'source_statements'
    )

@admin.register(PerjuryArgument)
class PerjuryArgumentAdmin(admin.ModelAdmin):
    list_display = ('trame', 'updated_at')
    search_fields = ('trame__titre',)
