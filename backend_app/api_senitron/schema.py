import graphene
from django.db.models import BigIntegerField
from django.db.models.functions import Cast
from graphene_django.types import DjangoObjectType
from .models import SenitronItem, SenitronItemAsset, SenitronStatus, TimelineItem

class SenitronStatusType(DjangoObjectType):
    class Meta:
        model = SenitronStatus
        fields = "__all__"

class SenitronItemType(DjangoObjectType):
    class Meta:
        model = SenitronItem
        fields = "__all__"

class SenitronItemAssetType(DjangoObjectType):
    class Meta:
        model = SenitronItemAsset
        fields = "__all__"
        
class TimelineItemType(DjangoObjectType):
    class Meta:
        model = TimelineItem
        fields = "__all__"
        

class Query(graphene.ObjectType):
    all_senitron_inventory_items = graphene.List(SenitronItemType)
    
    all_senitron_inventory_items_assets = graphene.List(SenitronItemAssetType)
    
    all_timeline_items = graphene.List(TimelineItemType)    

    def resolve_all_senitron_inventory_items(self, info, **kwargs):
        return SenitronItem.objects.annotate(
            item_number_int=Cast('item_number', BigIntegerField())
        ).order_by('-item_number_int')

    def resolve_all_senitron_inventory_items_assets(self, info, **kwargs):
        return SenitronItemAsset.objects.annotate(
            item_number_int=Cast('item_number', BigIntegerField())
        ).select_related('senitron_item', 'status').order_by('-item_number_int')
        
    def resolve_all_timeline_items(self, info, **kwargs):
        return TimelineItem.objects.all().order_by(
            '-date_actual_quantity', 
            '-date_actual_stock_on_hand', 
            '-date_actual_status_senitron', 
            '-date_actual_status_zoho'
        )

schema = graphene.Schema(query=Query)
