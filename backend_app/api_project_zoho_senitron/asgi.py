import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from api_zoho.ws_urls import websocket_urlpatterns
from api_senitron.ws_urls import websocket_senitron_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api_project_zoho_senitron.settings')
django.setup()

urlpatterns = websocket_urlpatterns + websocket_senitron_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            urlpatterns
        )
    ),
})