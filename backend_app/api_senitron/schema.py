import graphene
from django.db.models import BigIntegerField, Subquery, OuterRef, Count, F, Q
from django.db.models.functions import Cast, JSONObject, Coalesce
from django.contrib.postgres.aggregates import ArrayAgg
from graphene_django.types import DjangoObjectType
from django.utils import timezone
from rest_framework import serializers
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
        
        
class StatusType(graphene.ObjectType):
    id = graphene.Int()
    name = graphene.String()
    
        

class AssetType(graphene.ObjectType):
    id = graphene.Int()
    serial_number = graphene.String()
    alt_serial = graphene.String()
    first_seen = graphene.DateTime()
    last_seen = graphene.DateTime()
    last_seen_antenna = graphene.String()
    last_zone = graphene.String()
    handheld_reader = graphene.String()
    handheld_last_seen = graphene.DateTime()
    static_zone = graphene.String()
    static_zone_last_update = graphene.DateTime()
    receiving_date = graphene.DateTime()
    current_units = graphene.Int()
    storage_unit = graphene.String()
    adjust_qty = graphene.Int()
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()
    epc = graphene.String()
    text3 = graphene.String()
    status = graphene.Field(StatusType)
    
    
class SenitronItemAssetGroupType(graphene.ObjectType):
    item_number = graphene.String()
    count = graphene.Int()
    senitron_item = graphene.Field(lambda: SenitronItemType)  
    assets = graphene.List(AssetType)
    
    

# SERIALIZERS 

class DateTimeFieldNoFormat(serializers.Field):
    def to_representation(self, value):
        return value

class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = SenitronStatus
        fields = ['id', 'name']

class AssetSerializer(serializers.ModelSerializer):
    status = StatusSerializer()
    first_seen = DateTimeFieldNoFormat()
    last_seen = DateTimeFieldNoFormat()
    handheld_last_seen = DateTimeFieldNoFormat()
    static_zone_last_update = DateTimeFieldNoFormat()
    receiving_date = DateTimeFieldNoFormat()
    created_at = DateTimeFieldNoFormat()
    updated_at = DateTimeFieldNoFormat()

    class Meta:
        model = SenitronItemAsset
        fields = [
            'id',
            'serial_number',
            'alt_serial',
            'first_seen',
            'last_seen',
            'last_seen_antenna',
            'last_zone',
            'handheld_reader',
            'handheld_last_seen',
            'static_zone',
            'static_zone_last_update',
            'receiving_date',
            'current_units',
            'storage_unit',
            'adjust_qty',
            'created_at',
            'updated_at',
            'epc',
            'text3',
            'status',
        ]

class SenitronItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SenitronItem
        fields = ['id', 'item_number', 'tags_count', 'qty']

class SenitronItemAssetGroupSerializer(serializers.Serializer):
    item_number = serializers.CharField()
    count = serializers.IntegerField()
    senitron_item = SenitronItemSerializer()
    assets = AssetSerializer(many=True)
    
    
    
# QUERY
        

class Query(graphene.ObjectType):
    all_senitron_inventory_items = graphene.List(SenitronItemType)
    
    # all_senitron_inventory_items_assets = graphene.List(SenitronItemAssetType)
    
    all_senitron_inventory_items_assets = graphene.List(SenitronItemAssetGroupType)
    
    all_timeline_items = graphene.List(TimelineItemType)    
    

    def resolve_all_senitron_inventory_items(self, info, **kwargs):
        return SenitronItem.objects.annotate(
            item_number_int=Cast('item_number', BigIntegerField())
        ).order_by('-item_number_int')
        

    def resolve_all_senitron_inventory_items_assets(self, info, **kwargs):
        item_not_read = SenitronItemAsset.objects.filter(read=False).exists()
        if item_not_read:
            SenitronItemAsset.objects.all().update(read=True, date_read=timezone.now())
        
        assets = SenitronItemAsset.objects.select_related('status', 'senitron_item').annotate(
            order_date=Coalesce('last_seen', 'updated_at')
        ).order_by('-order_date')
        
        grouped_data = {}
        for asset in assets:
            item_number = asset.item_number
            if item_number not in grouped_data:
                grouped_data[item_number] = {
                    'item_number': item_number,
                    'count': 0,
                    'senitron_item': asset.senitron_item,
                    'assets': []
                }
            grouped_data[item_number]['count'] += 1
            grouped_data[item_number]['assets'].append(asset)
        
        serialized_data = SenitronItemAssetGroupSerializer(list(grouped_data.values()), many=True)
        
        result = []
        for group_data in serialized_data.data:
            senitron_item_data = group_data['senitron_item']
            senitron_item_instance = SenitronItemType(**senitron_item_data) if senitron_item_data else None
            
            assets = [AssetType(**asset_data) for asset_data in group_data['assets']]
            
            senitron_item_group = SenitronItemAssetGroupType(
                item_number=group_data['item_number'],
                count=group_data['count'],
                senitron_item=senitron_item_instance,
                assets=assets
            )
            result.append(senitron_item_group)
        
        return result
        
        # return SenitronItemAsset.objects.annotate(
        #     item_number_int=Cast('item_number', BigIntegerField())
        # ).select_related('senitron_item', 'status').order_by('-item_number_int')
        
    def resolve_all_timeline_items(self, info, **kwargs):
        return TimelineItem.objects.filter(
             Q(zoho_item__sku__isnull=False) & ~Q(zoho_item__sku='') &
                (~Q(text__icontains='stock on hand') | Q(date_actual_stock_on_hand__isnull=False)) &
                (~Q(text__icontains='status') | Q(date_actual_status_zoho__isnull=False)
                )
            ).annotate(
                order_date=Coalesce(
                    F('date_actual_stock_on_hand'),
                    F('date_actual_status_zoho'),
                    F('date_actual_quantity'),
                    F('date_actual_status_senitron')
                )
            ).order_by('-order_date')

schema = graphene.Schema(query=Query)
