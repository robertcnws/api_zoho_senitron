import graphene
from django.db.models import BigIntegerField
from django.db.models.functions import Cast
from graphene_django.types import DjangoObjectType
from .models import LoginUser, ZohoInventoryItem, ZohoInventoryShipmentSalesOrder
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
        

class Query(graphene.ObjectType):
    all_login_users = graphene.List(LoginUserType)
    all_zoho_inventory_items = graphene.List(ZohoInventoryItemType)

    # Agrega los argumentos `start_date` y `end_date` para filtrar por rango de fechas
    all_zoho_inventory_sales_orders = graphene.List(
        ZohoInventoryShipmentSalesOrderType,
        start_date=graphene.String(required=False),  # Argumento opcional de fecha de inicio
        end_date=graphene.String(required=False)    # Argumento opcional de fecha de fin
    )

    def resolve_all_login_users(self, info, **kwargs):
        return LoginUser.objects.all()

    def resolve_all_zoho_inventory_items(self, info, **kwargs):
        # return ZohoInventoryItem.objects.all().order_by('-item_id')
        return ZohoInventoryItem.objects.annotate(
            item_id_int=Cast('item_id', BigIntegerField())
        ).order_by('-item_id_int')

    def resolve_all_zoho_inventory_sales_orders(self, info, start_date=None, end_date=None, **kwargs):
        # sales_orders = ZohoInventoryShipmentSalesOrder.objects.all().order_by('-salesorder_id')
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

schema = graphene.Schema(query=Query)
