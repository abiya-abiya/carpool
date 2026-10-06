"""
ASGI config for carpool project.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carpool.settings')

application = get_asgi_application()
