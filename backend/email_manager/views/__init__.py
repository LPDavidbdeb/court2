from .thread import (
    EmailThreadListView,
    EmailThreadDetailView,
    EmailSearchView,
    EmailThreadDeleteView,
    EmailThreadSaveView
)
from .email import (
    EmailDetailView,
    DownloadEmlView,
    EmailPrintableView,
    EmlUploadView,
)
from .quote import (
    QuoteDetailView,
    AddQuoteView,
    QuoteListView,
    QuoteDeleteView,
    QuoteUpdateView
)

__all__ = [
    # Thread views
    'EmailThreadListView',
    'EmailThreadDetailView',
    'EmailSearchView',
    'EmailThreadDeleteView',
    'EmailThreadSaveView',

    # Email views
    'EmailDetailView',
    'DownloadEmlView',
    'EmailPrintableView',
    'EmlUploadView',

    # Quote views
    'QuoteDetailView',
    'AddQuoteView',
    'QuoteListView',
    'QuoteDeleteView',
    'QuoteUpdateView',
]
