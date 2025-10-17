# project/urls.py
from django.urls import path  # Importa include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf.urls.static import static
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView
from .schema import schema
from . import views

app_name = 'api_zoho'

urlpatterns = [
    path("login/", views.login, name="login"),
    path("health_check/", views.health_check, name="health_check"),
    path("manage_user/<int:user_id>/", views.manage_user, name="manage_user"),
    path("delete_user/<int:user_id>/", views.delete_user, name="delete_user"),
    path("delete_users/", views.delete_users, name="delete_users"),
    path("connect/", views.zoho_api_connect, name="zoho_api_connect"),
    path("zoho_api_settings/", views.zoho_api_settings, name="zoho_api_settings"),
    path("generate_auth_url/", views.generate_auth_url, name="generate_auth_url"),
    path("get_refresh_token/", views.get_refresh_token, name="get_refresh_token"),
    path('load/inventory_items/', views.load_inventory_items, name='load_inventory_items'),
    path('load/inventory_sales_orders/', views.load_inventory_sales_orders, name='load_inventory_sales_orders'),
    # path('load/inventory_packages/', views.load_inventory_packages, name='load_inventory_packages'),
    path('load/inventory_shipments/', views.load_inventory_shipments, name='load_inventory_shipments'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('sync/senitron/', views.sync_with_senitron, name='sync_with_senitron'),
    path('create_zoho_sku_track_info/', views.create_zoho_sku_track_info, name='create_zoho_sku_track_info'),
    path('create_zoho_items_assets_track/', views.create_zoho_items_assets_track, name='create_zoho_items_assets_track'),
    path('ignore_selected_errors_zoho_items/', views.ignore_selected_errors_zoho_items, name='ignore_selected_errors_zoho_items'),
    path('set_manual_updating_jobs/', views.set_manual_updating_jobs, name='set_manual_updating_jobs'),
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True, schema=schema))),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
