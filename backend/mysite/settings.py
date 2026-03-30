"""
This file acts as a switcher for Django settings.

It reads the DJANGO_ENV environment variable to determine whether to load
local or remote settings.

- DJANGO_ENV=local (default): Loads settings for local development.
- DJANGO_ENV=remote: Loads settings for production.
"""

import os

# Default to 'local' if DJANGO_ENV is not set
environment = os.getenv('DJANGO_ENV', 'local')

if environment == 'remote':
    from .settings.remote import *
else:
    from .settings.local import *
