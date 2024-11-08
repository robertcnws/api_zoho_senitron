from .models import SenitronItem, SenitronItemAsset, SenitronStatus
from django.db.utils import IntegrityError
from django.utils import timezone
from datetime import datetime

def create_inventory_item_instance(logger, data):
    item_number = data.get('item_number')
    tags_count = data.get('tags_count')
    qty = data.get('qty')
    try:
        item, _ = SenitronItem.objects.update_or_create(
            item_number=item_number,
            defaults={
                'tags_count': tags_count,
                'qty': qty
            }
        )
        return item
    except IntegrityError:
        logger.error(f"Integrity error for item_number={item_number}. Skipping.")
        return None
    

def create_inventory_item_asset_instance(logger, data):
    item_number = data.get('item_number')
    serial_number = data.get('serial_number')
    alt_serial = data.get('alt_serial')
    aware_first_seen = None
    if data.get('first_seen') and data.get('first_seen').strip():
        try:
            first_seen = datetime.strptime(data.get('first_seen'), "%m/%d/%y %I:%M %p")
            aware_first_seen = timezone.make_aware(first_seen, timezone.get_current_timezone())
        except ValueError:
            aware_first_seen = None
    aware_last_seen = None
    if data.get('last_seen') and data.get('last_seen').strip():
        try:
            last_seen = datetime.strptime(data.get('last_seen'), "%m/%d/%y %I:%M %p")
            aware_last_seen = timezone.make_aware(last_seen, timezone.get_current_timezone())
        except ValueError:
            aware_last_seen = None
    last_seen_antenna = data.get('last_seen_antenna')
    last_zone = data.get('last_zone')
    handheld_reader = data.get('handheld_reader')
    aware_handheld_last_seen = None
    if data.get('handheld_last_seen') and data.get('handheld_last_seen').strip():
        try:
            handheld_last_seen = datetime.strptime(data.get('handheld_last_seen'), "%m/%d/%y %I:%M %p")
            aware_handheld_last_seen = timezone.make_aware(handheld_last_seen, timezone.get_current_timezone())
        except ValueError:
            aware_handheld_last_seen = None
    static_zone = data.get('static_zone')
    aware_static_zone_last_update = None
    if data.get('static_zone_last_update') and data.get('static_zone_last_update').strip():
        try:
            static_zone_last_update = datetime.strptime(data.get('static_zone_last_update'), "%m/%d/%y %I:%M %p")
            aware_static_zone_last_update = timezone.make_aware(static_zone_last_update, timezone.get_current_timezone())
        except ValueError:
            aware_static_zone_last_update = None
    aware_receiving_date = None
    if data.get('receiving_date') and data.get('receiving_date').strip():
        try:
            receiving_date = datetime.strptime(data.get('receiving_date'), "%m/%d/%y %I:%M %p")
            aware_receiving_date = timezone.make_aware(receiving_date, timezone.get_current_timezone())
        except ValueError:
            aware_receiving_date = None
    current_units = data.get('current_units')
    storage_unit = data.get('storage_unit')
    adjust_qty = data.get('adjust_qty')
    attr1 = data.get('attr1')
    attr2 = data.get('attr2')
    attr3 = data.get('attr3')
    attr4 = data.get('attr4')
    attr5 = data.get('attr5')
    attr6 = data.get('attr6')
    attr7 = data.get('attr7')
    attr8 = data.get('attr8')
    attr9 = data.get('attr9')
    attr10 = data.get('attr10')
    aware_created_at = None
    if data.get('created_at') and data.get('created_at').strip():
        try:
            created_at = datetime.strptime(data.get('created_at'), "%m/%d/%y %I:%M %p")
            aware_created_at = timezone.make_aware(created_at, timezone.get_current_timezone())
        except ValueError:
            aware_created_at = None
    aware_updated_at = None
    if data.get('updated_at') and data.get('updated_at').strip():
        try:
            updated_at = datetime.strptime(data.get('updated_at'), "%m/%d/%y %I:%M %p")
            aware_updated_at = timezone.make_aware(updated_at, timezone.get_current_timezone())
        except ValueError:
            aware_updated_at = None
    epc = data.get('epc')
    text3 = data.get('text3')
    status_json = data.get('status')
    try:
        status, _ = SenitronStatus.objects.update_or_create(
            name=status_json.get('name'), senitron_id=status_json.get('id')
        ) 
        senitron_item = SenitronItem.objects.filter(item_number=item_number).first() or None
        
        asset = SenitronItemAsset.objects.create(
                    item_number=item_number,
                    serial_number=serial_number,
                    alt_serial=alt_serial,
                    first_seen=aware_first_seen,
                    last_seen=aware_last_seen,
                    last_seen_antenna=last_seen_antenna,
                    last_zone=last_zone,
                    handheld_reader=handheld_reader,
                    handheld_last_seen=aware_handheld_last_seen,
                    static_zone=static_zone,
                    static_zone_last_update=aware_static_zone_last_update,
                    receiving_date=aware_receiving_date,
                    current_units=current_units,
                    storage_unit=storage_unit,
                    adjust_qty=adjust_qty,
                    attr1=attr1,
                    attr2=attr2,
                    attr3=attr3,
                    attr4=attr4,
                    attr5=attr5,
                    attr6=attr6,
                    attr7=attr7,
                    attr8=attr8,
                    attr9=attr9,
                    attr10=attr10,
                    created_at=aware_created_at,
                    updated_at=aware_updated_at,
                    epc=epc,
                    text3=text3,
                    status=status,
                    senitron_item=senitron_item,
                    read=False,
                    date_read=None
            )
        return asset
    except IntegrityError:
        logger.error(f"Integrity error for item_number={item_number}. Skipping.")
        return None
