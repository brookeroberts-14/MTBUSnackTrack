import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MTBUSolutions.settings')

from django.core.asgi import get_asgi_application
application = get_asgi_application()
