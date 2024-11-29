import graphene
from django.db.models import BigIntegerField
from django.db.models.functions import Cast
from graphene_django.types import DjangoObjectType
from django.db.models import Window, F
from django.db.models.functions import Lead, RowNumber
from .models import LoginUser, ZohoInventoryItem, ZohoInventoryShipmentSalesOrder, ZohoSkuTrackInfo, ZohoPackage, ZohoShipmentOrder, ZohoItemAssetsTrack
from .scalars import JSONScalar
from datetime import datetime
from django.utils import timezone

class LoginUserType(DjangoObjectType):
    class Meta:
        model = LoginUser
        fields = "__all__"

class ZohoInventoryItemType(DjangoObjectType):
    class Meta:
        model = ZohoInventoryItem
        fields = "__all__"

class ZohoInventoryShipmentSalesOrderType(DjangoObjectType):
    class Meta:
        model = ZohoInventoryShipmentSalesOrder
        fields = "__all__"
        
        
class ZohoSkuTrackInfoType(DjangoObjectType):
    class Meta:
        model = ZohoSkuTrackInfo
        fields = "__all__"
        

class ZohoShipmentOrderType(DjangoObjectType):
    class Meta:
        model = ZohoShipmentOrder
        fields = "__all__"
        
        
class ZohoPackageType(DjangoObjectType):
    class Meta:
        model = ZohoPackage
        fields = "__all__"
        
        
class DifferencesSerialsType(graphene.ObjectType):
    news = graphene.List(graphene.String, description="New serial numbers")
    losts = graphene.List(graphene.String, description="Lost serial numbers")
    
    
class HistoryDifferencesSerialsType(graphene.ObjectType):
    date = graphene.DateTime()
    differences = graphene.Field(DifferencesSerialsType, description="Differences between the serial numbers of the continuous assets")
    
    
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
        

class ZohoItemAssetsTrackType(DjangoObjectType):
    differences = graphene.Field(DifferencesSerialsType, description="Differences between the serial numbers of the continuous assets")
    historial_differences = graphene.List(HistoryDifferencesSerialsType, description="History of differences between the serial numbers of the continuous assets")
    class Meta:
        model = ZohoItemAssetsTrack
        fields = "__all__"
        
    assets = JSONScalar()
    
    assets_list = graphene.List(AssetType, description="List of assets")
    
    def resolve_assets_list(self, info):
        list_assets = []
        for asset in self.assets:
            new_asset = AssetType(
                id=asset.get('id', ''),
                serial_number=asset.get('serialNumber', ''),
                alt_serial=asset.get('altSerial', ''),
                first_seen=asset.get('firstSeen', ''),
                last_seen=asset.get('lastSeen', ''),
                last_seen_antenna=asset.get('lastSeenAntenna', ''),
                last_zone=asset.get('lastZone', ''),
                handheld_reader=asset.get('handheldReader', ''),
                handheld_last_seen=asset.get('handheldLastSeen', ''),
                static_zone=asset.get('staticZone', ''),
                static_zone_last_update=asset.get('staticZoneLastUpdate', ''),
                receiving_date=asset.get('receivingDate', ''),
                current_units=asset.get('currentUnits', ''),
                storage_unit=asset.get('storageUnit', ''),
                adjust_qty=asset.get('adjustQty', ''),
                created_at=asset.get('createdAt', ''),
                updated_at=asset.get('updatedAt', ''),
                epc=asset.get('epc', ''),
                text3=asset.get('text3', '')
            )
            list_assets.append(new_asset)
        return list_assets

    def resolve_assets(self, info):
        return self.assets
    
    def resolve_differences(self, info):
        if hasattr(self, 'next_assets') and self.next_assets:
            current_serials = set(
                asset['serialNumber'] for asset in self.assets 
                if 'serialNumber' in asset and asset['serialNumber']
            )
            next_serials = set(
                asset['serialNumber'] for asset in self.next_assets 
                if 'serialNumber' in asset and asset['serialNumber']
            )
            news = list(current_serials - next_serials)
            losts = list(next_serials - current_serials)
        else:
            news = []
            losts = []

        return DifferencesSerialsType(news=news, losts=losts)
    
    
    # def resolve_historial_differences(self, info):
    #     from django.utils import timezone
        
    #     prior_tracks = ZohoItemAssetsTrack.objects.filter(
    #         item_id=self.item_id,
    #         created_time__lt=self.created_time
    #     ).only('created_time', 'assets').order_by('created_time')  

    #     historial = []
    #     previous_serials = set()

    #     for track in prior_tracks:
            
    #         if timezone.is_naive(track.created_time):
    #             track_created_time = timezone.make_aware(
    #                 track.created_time, 
    #                 timezone.get_current_timezone()
    #             )
    #         else:
    #             track_created_time = track.created_time
            
    #         current_serials = set(
    #             asset.get('serialNumber') for asset in track.assets 
    #             if asset.get('serialNumber')
    #         )
            
    #         news = list(current_serials - previous_serials)
    #         losts = list(previous_serials - current_serials)
            
    #         historial.append(
    #             HistoryDifferencesSerialsType(
    #                 date=track_created_time,
    #                 differences=DifferencesSerialsType(news=news, losts=losts)
    #             )
    #         )
            
    #         previous_serials = current_serials
            
    #     historial.reverse()

    #     return historial
        

class Query(graphene.ObjectType):
    all_login_users = graphene.List(LoginUserType)
    all_zoho_inventory_items = graphene.List(ZohoInventoryItemType)
    all_zoho_sku_track_info = graphene.List(ZohoSkuTrackInfoType)
    all_zoho_packages = graphene.List(
        ZohoPackageType,
        shipment_id=graphene.String(required=False),
        package_id=graphene.String(required=False),
        list_packages_id=graphene.List(graphene.String, required=False)
    )
    all_zoho_shipment_orders = graphene.List(
        ZohoShipmentOrderType,
        start_date=graphene.String(required=False),  
        end_date=graphene.String(required=False)    
    )
    all_zoho_inventory_sales_orders = graphene.List(
        ZohoInventoryShipmentSalesOrderType,
        start_date=graphene.String(required=False),  
        end_date=graphene.String(required=False)    
    )
    all_zoho_item_assets_track = graphene.List(
        ZohoItemAssetsTrackType,
        item_id=graphene.String(required=False), 
        list_ids=graphene.List(graphene.String, required=False) 
    )
    

    def resolve_all_login_users(self, info, **kwargs):
        return LoginUser.objects.all().order_by('username')

    def resolve_all_zoho_inventory_items(self, info, **kwargs):
        return ZohoInventoryItem.objects.annotate(
            item_id_int=Cast('item_id', BigIntegerField())
        ).order_by('-item_id_int')
        
    def resolve_all_zoho_sku_track_info(self, info, **kwargs):
        return ZohoSkuTrackInfo.objects.all().order_by('date')
    
    def resolve_all_zoho_packages(self, info, shipment_id=None, package_id=None, list_packages_id=None, **kwargs):
        packages = ZohoPackage.objects.all().order_by('-date')
        if shipment_id:
            return packages.filter(shipment_id=shipment_id)
        if package_id:
            return packages.filter(package_id=package_id)
        if list_packages_id:
            return packages.filter(package_id__in=list_packages_id)
        return packages

    def resolve_all_zoho_inventory_sales_orders(self, info, start_date=None, end_date=None, **kwargs):
        sales_orders = ZohoInventoryShipmentSalesOrder.objects.annotate(
            salesorder_id_int=Cast('salesorder_id', BigIntegerField())
        ).order_by('-salesorder_id_int')
        
        if start_date and end_date:
            try:
                start_date_parsed = datetime.strptime(start_date, '%Y-%m-%d')
                end_date_parsed = datetime.strptime(end_date, '%Y-%m-%d')
                return sales_orders.filter(date__range=(start_date_parsed, end_date_parsed))
            except ValueError:
                raise Exception("Formato de fecha inválido. Usa 'YYYY-MM-DD'.")
        
        return sales_orders
    
    def resolve_all_zoho_shipment_orders(self, info, start_date=None, end_date=None, **kwargs):
        shipment_orders = ZohoShipmentOrder.objects.annotate(
            shipment_id_int=Cast('shipment_id', BigIntegerField())
        ).order_by('-shipment_id_int')
        
        if start_date and end_date:
            try:
                start_date_parsed = datetime.strptime(start_date, '%Y-%m-%d')
                end_date_parsed = datetime.strptime(end_date, '%Y-%m-%d')
                return shipment_orders.filter(date__range=(start_date_parsed, end_date_parsed))
            except ValueError:
                raise Exception("Formato de fecha inválido. Usa 'YYYY-MM-DD'.")
            
        elif start_date:
            try:
                start_date_parsed = datetime.strptime(start_date, '%Y-%m-%d')
                return shipment_orders.filter(date__gte=start_date_parsed)
            except ValueError:
                raise Exception("Formato de fecha inválido. Usa 'YYYY-MM-DD'.")
        
        elif end_date:
            try:
                end_date_parsed = datetime.strptime(end_date, '%Y-%m-%d')
                return shipment_orders.filter(date__lte=end_date_parsed)
            except ValueError:
                raise Exception("Formato de fecha inválido. Usa 'YYYY-MM-DD'.")
        
        return shipment_orders
    
    def resolve_all_zoho_item_assets_track(self, info, item_id=None, list_ids=None, **kwargs):
        from itertools import groupby
        from operator import attrgetter
        from django.utils import timezone

        if item_id:
            queryset = ZohoItemAssetsTrack.objects.filter(item_id=item_id)
        elif list_ids:
            queryset = ZohoItemAssetsTrack.objects.filter(item_id__in=list_ids)
        else:
            queryset = ZohoItemAssetsTrack.objects.all()

        queryset = queryset.order_by('item_id', 'created_time', 'id')
        tracks = list(queryset)
        grouped = groupby(tracks, key=attrgetter('item_id'))
        result = []

        for item_id, group in grouped:
            group_list = list(group)
            historial = []
            previous_serials = set()
            for track in group_list:
                if timezone.is_naive(track.created_time):
                    track_created_time = timezone.make_aware(
                        track.created_time, 
                        timezone.get_current_timezone()
                    )
                else:
                    track_created_time = track.created_time
                current_serials = set(
                    asset.get('serialNumber') for asset in track.assets 
                    if asset.get('serialNumber')
                )
                news = list(current_serials - previous_serials)
                losts = list(previous_serials - current_serials)
                historial.append(
                    HistoryDifferencesSerialsType(
                        date=track_created_time,
                        differences=DifferencesSerialsType(news=news, losts=losts)
                    )
                )
                previous_serials = current_serials
            historial.reverse()
            most_recent_track = group_list[-1]
            most_recent_track.historial_differences = historial
            result.append(most_recent_track)

        return result

schema = graphene.Schema(query=Query)
