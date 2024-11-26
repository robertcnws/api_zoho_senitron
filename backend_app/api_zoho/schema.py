import graphene
from django.db.models import BigIntegerField
from django.db.models.functions import Cast
from graphene_django.types import DjangoObjectType
from django.db.models import Window, F
from django.db.models.functions import Lead
from .models import LoginUser, ZohoInventoryItem, ZohoInventoryShipmentSalesOrder, ZohoSkuTrackInfo, ZohoPackage, ZohoShipmentOrder, ZohoItemAssetsTrack
from .scalars import JSONScalar
from datetime import datetime

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
        

class ZohoItemAssetsTrackType(DjangoObjectType):
    differences = graphene.Field(DifferencesSerialsType, description="Differences between the serial numbers of the continuous assets")
    class Meta:
        model = ZohoItemAssetsTrack
        fields = "__all__"
        
    assets = JSONScalar()

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
        item_id=graphene.String(required=False) 
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
        
        return shipment_orders
    
    def resolve_all_zoho_item_assets_track(self, info, item_id=None, **kwargs):
        if item_id:
            queryset = ZohoItemAssetsTrack.objects.filter(item_id=item_id)
        else:
            queryset = ZohoItemAssetsTrack.objects.all()
        
        queryset = queryset.order_by('item_id', 'created_time', 'id').annotate(
            next_assets=Window(
                expression=Lead('assets', offset=1),
                partition_by=[F('item_id')],
                order_by=[F('created_time').asc(), F('id').asc()]
            )
        )
        
        return queryset

schema = graphene.Schema(query=Query)
