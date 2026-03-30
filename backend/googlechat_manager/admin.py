from django.contrib import admin
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from .models import ChatParticipant, ChatThread, ChatMessage, ChatSubject, SubjectGroup, ChatSequence

class ChatSequenceAdminForm(forms.ModelForm):
    messages = forms.ModelMultipleChoiceField(
        queryset=ChatMessage.objects.all().order_by('-timestamp'),
        widget=FilteredSelectMultiple(
            verbose_name='Messages',
            is_stacked=False
        ),
        help_text="Use the filter to search for messages by content. Hold command/control to select multiple."
    )

    class Meta:
        model = ChatSequence
        fields = ['title', 'messages']

@admin.register(ChatSequence)
class ChatSequenceAdmin(admin.ModelAdmin):
    form = ChatSequenceAdminForm
    list_display = ('title', 'start_date', 'end_date', 'created_at')
    search_fields = ('title',)
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.pk:
            obj.update_dates()

# Basic admin registrations for other models for browsability
admin.site.register(ChatParticipant)
admin.site.register(ChatThread)
@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'sender', 'text_content')
    list_filter = ('sender', 'thread')
    search_fields = ('text_content',)
    ordering = ('-timestamp',)

admin.site.register(ChatSubject)
admin.site.register(SubjectGroup)