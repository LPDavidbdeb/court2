from django.contrib import admin
from .models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """
    Admin view for the Event model.
    """
    list_display = ('__str__', 'date', 'parent')
    list_filter = ('parent', 'date')
    search_fields = ('explanation', 'email_quote')
    
    raw_id_fields = ('parent', 'linked_email')

    fieldsets = (
        ('Core Information', {
            'fields': ('parent', 'explanation')
        }),
        ('Date and Time', {
            'fields': ('date',)
        }),
        # 'linked_photos' is removed from here because it uses a custom through model
        ('Linked Evidence', {
            'fields': ('linked_email', 'email_quote')
        }),
    )

    # 'filter_horizontal' cannot be used with a ManyToManyField that has a through model.
    # To manage photo links, you would typically use an InlineModelAdmin.
    # filter_horizontal = ('linked_photos',)
