# project/urls.py
from django.urls import path  # Importa include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf.urls.static import static
from django.conf import settings
from . import views

app_name = 'api_zoho'

urlpatterns = [
    path("connect/", views.zoho_api_connect, name="zoho_api_connect"),
    path("zoho_api_settings/", views.zoho_api_settings, name="zoho_api_settings"),
    path("generate_auth_url/", views.generate_auth_url, name="generate_auth_url"),
    path("get_refresh_token/", views.get_refresh_token, name="get_refresh_token"),
    path('load/inventory_items/', views.load_inventory_items, name='load_inventory_items'),
    path('load/inventory_shipment_orders/', views.load_inventory_shipment_orders, name='load_inventory_shipment_orders'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
