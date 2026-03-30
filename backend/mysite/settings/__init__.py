import os
from .base import *

# Check the environment variable to decide which settings to load.
env = os.getenv('DJANGO_ENV', 'local')

if env == 'local':
    try:
        from .local import *
    except ImportError:
        pass
elif env == 'remote':
    try:
        from .remote import *
    except ImportError:
        pass
