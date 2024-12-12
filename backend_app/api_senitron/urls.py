from django.urls import path
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt
from . import views
from .schema import schema


app_name = 'api_senitron'

urlpatterns = [
    path('load/senitron_inventory_items/', views.load_senitron_inventory_items, name='load_senitron_inventory_items'),
    path('load/senitron_inventory_item_assets/', views.load_senitron_inventory_item_assets, name='load_senitron_inventory_item_assets'),
    path('load/senitron_inventory_item_assets/logs/', views.load_senitron_inventory_item_assets_logs, name='load_senitron_inventory_item_assets_logs'),
    path('notifications/mark_all_as_read/', views.notifications_mark_all_as_read, name='notifications_mark_all_as_read'),
    path('notification/mark_as_read/<int:notification_id>/', views.notification_mark_as_read, name='notification_mark_as_read'),
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True, schema=schema))),
]
