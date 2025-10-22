# schema.py
import graphene
from django.db.models import F, Q
from django.db.models.functions import Coalesce, TruncDate
from graphene_django.types import DjangoObjectType
from django.utils import timezone
from datetime import date
from .models import (
    SenitronItem,
    SenitronItemAsset,
    SenitronStatus,
    TimelineItem,
    SenitronItemAssetLogs,
    Notification,
    NotificationUser,
)
from api_zoho.models import JobsUpdatingTimes, LoginUser
from utils.graphql_perf import fetch_all_streamed
from utils.graphql_cache import get_or_build_list

class SenitronStatusType(DjangoObjectType):
    class Meta:
        model = SenitronStatus
        fields = "__all__"

class NotificationType(DjangoObjectType):
    class Meta:
        model = Notification
        fields = "__all__"

class LoginUserType(DjangoObjectType):
    class Meta:
        model = LoginUser
        fields = "__all__"

class NotificationUserType(DjangoObjectType):
    notification = graphene.Field(NotificationType)
    user = graphene.Field(LoginUserType)
    class Meta:
        model = NotificationUser
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

class JobsUpdatingTimesType(DjangoObjectType):
    class Meta:
        model = JobsUpdatingTimes
        fields = "__all__"

class SenitronItemAssetLogsType(DjangoObjectType):
    class Meta:
        model = SenitronItemAssetLogs
        fields = "__all__"

class GroupedLogsType(graphene.ObjectType):
    item_number = graphene.String()
    date = graphene.Date()
    logs = graphene.List(SenitronItemAssetLogsType)

class Query(graphene.ObjectType):
    all_senitron_inventory_items = graphene.List(SenitronItemType)
    all_senitron_inventory_items_assets = graphene.List(SenitronItemAssetGroupType)
    all_timeline_items = graphene.List(TimelineItemType)
    all_jobs_updating_times = graphene.Field(JobsUpdatingTimesType, id=graphene.Int())
    all_senitron_grouped_logs = graphene.List(GroupedLogsType, start_date=graphene.Date(required=False))
    all_notification_user = graphene.List(NotificationUserType, username=graphene.String(required=False))

    # OPTIMIZADO: sin annotate (conflicta), orden con índice y solo columnas necesarias
    def resolve_all_senitron_inventory_items(self, info, **kwargs):
        qs = (
            SenitronItem.objects
            .only(  # ajusta esta lista a los campos que realmente usas en el frontend
                "id",
                "item_number",
                "item_number_int",
                "qty",
                "tags_count",
            )
            .order_by(
                F("item_number_int").desc(nulls_last=True),
                F("item_number").desc(),
            )
        )
        return get_or_build_list(
            "gql:all_senitron_inventory_items:v3",
            lambda: fetch_all_streamed(qs, chunk_size=1000),
            ttl=180,
        )

    def resolve_all_senitron_inventory_items_assets(self, info, **kwargs):
        unread = SenitronItemAsset.objects.filter(read=False)
        if unread.exists():
            unread.update(read=True, date_read=timezone.now())

        qs = (
            SenitronItemAsset.objects
            .select_related("status", "senitron_item")
            .annotate(order_date=Coalesce("last_seen", "updated_at"))
            .order_by("item_number", F("order_date").desc(nulls_last=True), "id")
        )

        result = []
        current_item = None
        current_assets = []
        current_count = 0
        current_senitron_item = None

        for asset in qs.iterator(chunk_size=1000):
            if current_item is not None and asset.item_number != current_item:
                assets_out = []
                for a in current_assets:
                    st = a.status
                    assets_out.append(
                        AssetType(
                            id=a.id,
                            serial_number=a.serial_number,
                            alt_serial=a.alt_serial,
                            first_seen=a.first_seen,
                            last_seen=a.last_seen,
                            last_seen_antenna=a.last_seen_antenna,
                            last_zone=a.last_zone,
                            handheld_reader=a.handheld_reader,
                            handheld_last_seen=a.handheld_last_seen,
                            static_zone=a.static_zone,
                            static_zone_last_update=a.static_zone_last_update,
                            receiving_date=a.receiving_date,
                            current_units=int(a.current_units) if a.current_units is not None else None,
                            storage_unit=str(a.storage_unit) if a.storage_unit is not None else None,
                            adjust_qty=a.adjust_qty,
                            created_at=a.created_at,
                            updated_at=a.updated_at,
                            epc=a.epc,
                            text3=a.text3,
                            status=StatusType(id=st.id, name=st.name) if st else None,
                        )
                    )
                result.append(
                    SenitronItemAssetGroupType(
                        item_number=current_item,
                        count=current_count,
                        senitron_item=current_senitron_item,
                        assets=assets_out,
                    )
                )
                current_assets = []
                current_count = 0
                current_senitron_item = None

            current_item = asset.item_number
            current_count += 1
            if current_senitron_item is None:
                current_senitron_item = asset.senitron_item
            current_assets.append(asset)

        if current_item is not None:
            assets_out = []
            for a in current_assets:
                st = a.status
                assets_out.append(
                    AssetType(
                        id=a.id,
                        serial_number=a.serial_number,
                        alt_serial=a.alt_serial,
                        first_seen=a.first_seen,
                        last_seen=a.last_seen,
                        last_seen_antenna=a.last_seen_antenna,
                        last_zone=a.last_zone,
                        handheld_reader=a.handheld_reader,
                        handheld_last_seen=a.handheld_last_seen,
                        static_zone=a.static_zone,
                        static_zone_last_update=a.static_zone_last_update,
                        receiving_date=a.receiving_date,
                        current_units=int(a.current_units) if a.current_units is not None else None,
                        storage_unit=str(a.storage_unit) if a.storage_unit is not None else None,
                        adjust_qty=a.adjust_qty,
                        created_at=a.created_at,
                        updated_at=a.updated_at,
                        epc=a.epc,
                        text3=a.text3,
                        status=StatusType(id=st.id, name=st.name) if st else None,
                    )
                )
            result.append(
                SenitronItemAssetGroupType(
                    item_number=current_item,
                    count=current_count,
                    senitron_item=current_senitron_item,
                    assets=assets_out,
                )
            )

        return get_or_build_list(
            "gql:all_senitron_inventory_items_assets:v2",
            lambda: result,
            ttl=180,
        )

    def resolve_all_timeline_items(self, info, **kwargs):
        qs = (
            TimelineItem.objects
            .filter(
                Q(zoho_item__sku__isnull=False) & ~Q(zoho_item__sku="") &
                (~Q(text__icontains="stock on hand") | Q(date_actual_stock_on_hand__isnull=False)) &
                (~Q(text__icontains="status") | Q(date_actual_status_zoho__isnull=False))
            )
            .annotate(order_date=Coalesce(F("date_actual_stock_on_hand"), F("date_actual_status_zoho"), F("date_actual_quantity"), F("date_actual_status_senitron")))
            .order_by(F("order_date").desc(nulls_last=True))[:100]
        )
        return get_or_build_list(
            "gql:all_timeline_items:v2",
            lambda: fetch_all_streamed(qs, chunk_size=1000),
            ttl=180,
        )

    def resolve_all_jobs_updating_times(self, info, **kwargs):
        return JobsUpdatingTimes.objects.last()

    def resolve_all_senitron_grouped_logs(self, info, start_date=None, **kwargs):
        qs = (
            SenitronItemAssetLogs.objects
            .filter(~Q(current_status_id=F("last_status_id")))
            .annotate(date=TruncDate("created_time"))
        )
        if start_date:
            qs = qs.filter(date=start_date)
        qs = qs.order_by("item_number", "date", "id")

        result = []
        cur_item = None
        cur_date = None
        cur_logs = []

        for log in qs.iterator(chunk_size=1000):
            if cur_item is not None and (log.item_number != cur_item or log.date != cur_date):
                result.append(GroupedLogsType(item_number=cur_item, date=cur_date, logs=cur_logs))
                cur_logs = []
            cur_item = log.item_number
            cur_date = log.date
            cur_logs.append(log)

        if cur_item is not None:
            result.append(GroupedLogsType(item_number=cur_item, date=cur_date, logs=cur_logs))

        return get_or_build_list(
            f"gql:all_senitron_grouped_logs:{start_date}:v2",
            lambda: result,
            ttl=180,
        )

    def resolve_all_notification_user(self, info, username=None, **kwargs):
        qs = NotificationUser.objects.select_related("notification", "user").order_by("-created_at")
        if username:
            qs = qs.filter(user__username=username)
        qs = qs[:100]
        return get_or_build_list(
            f"gql:all_notification_user:{username}:v2",
            lambda: fetch_all_streamed(qs, chunk_size=1000),
            ttl=180,
        )

schema = graphene.Schema(query=Query)
