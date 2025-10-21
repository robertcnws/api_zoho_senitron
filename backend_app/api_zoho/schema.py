# schema.py
import graphene
from django.db.models import F
from itertools import groupby
from operator import attrgetter
from graphene_django.types import DjangoObjectType
from datetime import date
from django.utils import timezone
from django.core.cache import cache
from .models import LoginUser, ZohoInventoryItem, ZohoInventoryShipmentSalesOrder, ZohoSkuTrackInfo, ZohoPackage, ZohoShipmentOrder, ZohoItemAssetsTrack, ManualUpdatingJobs
from .scalars import JSONScalar
from utils.graphql_perf import fetch_all_streamed
from utils.graphql_cache import get_or_build_list

class LoginUserType(DjangoObjectType):
    class Meta:
        model = LoginUser
        fields = "__all__"

class ManualUpdatingJobsType(DjangoObjectType):
    class Meta:
        model = ManualUpdatingJobs
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
    news = graphene.List(graphene.String)
    losts = graphene.List(graphene.String)

class HistoryDifferencesSerialsType(graphene.ObjectType):
    date = graphene.DateTime()
    differences = graphene.Field(DifferencesSerialsType)

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
    differences = graphene.Field(DifferencesSerialsType)
    historial_differences = graphene.List(HistoryDifferencesSerialsType)
    class Meta:
        model = ZohoItemAssetsTrack
        fields = "__all__"
    assets = JSONScalar()
    assets_list = graphene.List(AssetType)
    def resolve_assets_list(self, info):
        assets = self.assets or []
        g = dict.get
        return [AssetType(
            id=g(a,'id',''),
            serial_number=g(a,'serialNumber',''),
            alt_serial=g(a,'altSerial',''),
            first_seen=g(a,'firstSeen',''),
            last_seen=g(a,'lastSeen',''),
            last_seen_antenna=g(a,'lastSeenAntenna',''),
            last_zone=g(a,'lastZone',''),
            handheld_reader=g(a,'handheldReader',''),
            handheld_last_seen=g(a,'handheldLastSeen',''),
            static_zone=g(a,'staticZone',''),
            static_zone_last_update=g(a,'staticZoneLastUpdate',''),
            receiving_date=g(a,'receivingDate',''),
            current_units=g(a,'currentUnits',''),
            storage_unit=g(a,'storageUnit',''),
            adjust_qty=g(a,'adjustQty',''),
            created_at=g(a,'createdAt',''),
            updated_at=g(a,'updatedAt',''),
            epc=g(a,'epc',''),
            text3=g(a,'text3','')
        ) for a in assets]
    def resolve_assets(self, info):
        return self.assets
    def resolve_differences(self, info):
        if hasattr(self, 'next_assets') and self.next_assets:
            cur = {a.get('serialNumber') for a in (self.assets or []) if a.get('serialNumber')}
            nxt = {a.get('serialNumber') for a in (self.next_assets or []) if a.get('serialNumber')}
            return DifferencesSerialsType(news=list(cur - nxt), losts=list(nxt - cur))
        return DifferencesSerialsType(news=[], losts=[])

class Query(graphene.ObjectType):
    all_login_users = graphene.List(LoginUserType)
    all_zoho_inventory_items = graphene.List(ZohoInventoryItemType)
    all_zoho_sku_track_info = graphene.List(ZohoSkuTrackInfoType)
    all_zoho_packages = graphene.List(ZohoPackageType, shipment_id=graphene.String(required=False), package_id=graphene.String(required=False), list_packages_id=graphene.List(graphene.String, required=False))
    all_zoho_shipment_orders = graphene.List(ZohoShipmentOrderType, start_date=graphene.String(required=False), end_date=graphene.String(required=False))
    all_zoho_inventory_sales_orders = graphene.List(ZohoInventoryShipmentSalesOrderType, start_date=graphene.String(required=False), end_date=graphene.String(required=False))
    all_zoho_item_assets_track = graphene.List(ZohoItemAssetsTrackType, item_id=graphene.String(required=False), list_ids=graphene.List(graphene.String, required=False))
    all_manual_updating_jobs = graphene.Field(ManualUpdatingJobsType, id=graphene.Int())

    def resolve_all_login_users(self, info, **kwargs):
        return LoginUser.objects.all().order_by('username')

    def resolve_all_zoho_inventory_items(self, info, **kwargs):
        qs = ZohoInventoryItem.objects.all().order_by(F('item_id_int').desc(nulls_last=True), F('item_id').desc())
        return get_or_build_list("gql:all_zoho_inventory_items:v3", lambda: fetch_all_streamed(qs, chunk_size=1000), ttl=180)

    def resolve_all_zoho_sku_track_info(self, info, **kwargs):
        qs = ZohoSkuTrackInfo.objects.all().order_by('date')
        return get_or_build_list("gql:all_zoho_sku_track_info:v3", lambda: fetch_all_streamed(qs, chunk_size=1000), ttl=180)

    def resolve_all_zoho_packages(self, info, shipment_id=None, package_id=None, list_packages_id=None, **kwargs):
        base = ZohoPackage.objects.all().order_by('-date')
        if shipment_id:
            return base.filter(shipment_id=shipment_id).iterator(chunk_size=1000)
        if package_id:
            return base.filter(package_id=package_id).iterator(chunk_size=1000)
        if list_packages_id:
            return base.filter(package_id__in=list_packages_id).iterator(chunk_size=1000)
        return get_or_build_list("gql:all_zoho_packages:v3", lambda: fetch_all_streamed(base, chunk_size=1000), ttl=120)

    def resolve_all_zoho_inventory_sales_orders(self, info, start_date=None, end_date=None, **kwargs):
        qs = ZohoInventoryShipmentSalesOrder.objects.all().order_by(F('salesorder_id_int').desc(nulls_last=True), F('salesorder_id').desc())
        if start_date and end_date:
            y1,m1,d1 = map(int, start_date.split('-'))
            y2,m2,d2 = map(int, end_date.split('-'))
            return qs.filter(date__range=(date(y1,m1,d1), date(y2,m2,d2))).iterator(chunk_size=1000)
        return get_or_build_list(f"gql:all_zoho_inventory_sales_orders:{start_date}:{end_date}:v3", lambda: fetch_all_streamed(qs, chunk_size=1000), ttl=180)

    def resolve_all_zoho_shipment_orders(self, info, start_date=None, end_date=None, **kwargs):
        qs = ZohoShipmentOrder.objects.all().order_by(F('shipment_id_int').desc(nulls_last=True), F('shipment_id').desc())
        if start_date and end_date:
            y1,m1,d1 = map(int, start_date.split('-'))
            y2,m2,d2 = map(int, end_date.split('-'))
            return qs.filter(date__range=(date(y1,m1,d1), date(y2,m2,d2))).iterator(chunk_size=1000)
        elif start_date:
            y,m,d = map(int, start_date.split('-'))
            return qs.filter(date__gte=date(y,m,d)).iterator(chunk_size=1000)
        elif end_date:
            y,m,d = map(int, end_date.split('-'))
            return qs.filter(date__lte=date(y,m,d)).iterator(chunk_size=1000)
        return get_or_build_list(f"gql:all_zoho_shipment_orders:{start_date}:{end_date}:v3", lambda: fetch_all_streamed(qs, chunk_size=1000), ttl=180)

    def resolve_all_zoho_item_assets_track(self, info, item_id=None, list_ids=None, **kwargs):
        qs = ZohoItemAssetsTrack.objects.all()
        if item_id:
            qs = qs.filter(item_id=item_id)
        elif list_ids:
            qs = qs.filter(item_id__in=list_ids)
        qs = qs.order_by('item_id', 'created_time', 'id')
        result = []
        cur_item = None
        previous_serials = set()
        historial = []
        last_track = None
        for track in qs.iterator(chunk_size=1000):
            if cur_item is not None and track.item_id != cur_item:
                if last_track:
                    historial.reverse()
                    last_track.historial_differences = historial
                    result.append(last_track)
                historial = []
                previous_serials = set()
            cur_item = track.item_id
            current_serials = {a.get('serialNumber') for a in (track.assets or []) if a.get('serialNumber')}
            news = list(current_serials - previous_serials)
            losts = list(previous_serials - current_serials)
            track_created_time = track.created_time
            if timezone.is_naive(track_created_time):
                track_created_time = timezone.make_aware(track_created_time, timezone.get_current_timezone())
            historial.append(HistoryDifferencesSerialsType(date=track_created_time, differences=DifferencesSerialsType(news=news, losts=losts)))
            previous_serials = current_serials
            last_track = track
        if last_track:
            historial.reverse()
            last_track.historial_differences = historial
            result.append(last_track)
        return get_or_build_list(f"gql:all_zoho_item_assets_track:{item_id}:{','.join(list_ids or [])}:v3", lambda: result, ttl=180)

    def resolve_all_manual_updating_jobs(self, info, id=None, **kwargs):
        if id:
            return ManualUpdatingJobs.objects.filter(id=id).first()
        return ManualUpdatingJobs.objects.first()

schema = graphene.Schema(query=Query)
