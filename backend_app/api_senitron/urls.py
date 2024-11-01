from django.urls import path
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt
from . import views
from .schema import schema


app_name = 'api_senitron'

urlpatterns = [
    path('load/senitron_inventory_items/', views.load_senitron_inventory_items, name='load_senitron_inventory_items'),
    path('load/senitron_inventory_item_assets/', views.load_senitron_inventory_item_assets, name='load_senitron_inventory_item_assets'),
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True, schema=schema))),
]
