# model_serializer.py

from typing import Optional, Dict, Any

# Helpers
def _iso(dt) -> Optional[str]:
    return dt.isoformat() if dt else None

def _to_float(v) -> Optional[float]:
    return float(v) if v is not None else None

def _to_int(v) -> Optional[int]:
    return int(v) if v is not None else None


# ========== SenitronItem ==========
def _senitron_item_to_message_dict(it) -> Dict[str, Any]:
    return {
        "itemNumber": it.item_number,
        "tagsCount": it.tags_count,
        "qty": it.qty,
    }


# ========== SenitronStatus ==========
def _senitron_status_to_message_dict(st) -> Dict[str, Any]:
    return {
        "senitronId": _to_int(st.senitron_id),
        "name": st.name,
    }


# ========== SenitronItemAsset ==========
def _senitron_item_asset_to_message_dict(a) -> Dict[str, Any]:
    status_obj = a.status  # FK (puede ser None)
    sen_item = a.senitron_item  # FK (puede ser None)

    return {
        "serialNumber": a.serial_number,
        "itemNumber": a.item_number,
        "altSerial": a.alt_serial,
        "firstSeen": _iso(a.first_seen),
        "lastSeen": _iso(a.last_seen),
        "lastSeenAntenna": a.last_seen_antenna,
        "lastZone": a.last_zone,
        "handheldReader": a.handheld_reader,
        "handheldLastSeen": _iso(a.handheld_last_seen),
        "staticZone": a.static_zone,
        "staticZoneLastUpdate": _iso(a.static_zone_last_update),
        "receivingDate": _iso(a.receiving_date),
        "currentUnits": _to_float(a.current_units),
        "storageUnit": _to_float(a.storage_unit),
        "adjustQty": _to_int(a.adjust_qty),
        "attr1": a.attr1,
        "attr2": a.attr2,
        "attr3": a.attr3,
        "attr4": a.attr4,
        "attr5": a.attr5,
        "attr6": a.attr6,
        "attr7": a.attr7,
        "attr8": a.attr8,
        "attr9": a.attr9,
        "attr10": a.attr10,
        "createdAt": _iso(a.created_at),
        "updatedAt": _iso(a.updated_at),
        "epc": a.epc,
        "text3": a.text3,
        "status": (
            {
                "senitronId": _to_int(status_obj.senitron_id),
                "name": status_obj.name,
            } if status_obj else None
        ),
        "senitronItem": (
            {
                "itemNumber": sen_item.item_number,
                "tagsCount": sen_item.tags_count,
                "qty": sen_item.qty,
            } if sen_item else None
        ),
        "read": bool(a.read),
        "dateRead": _iso(a.date_read),
    }


# ========== TimelineItem ==========
def _timeline_item_to_message_dict(tl) -> Dict[str, Any]:
    prev_status = tl.previous_status_senitron
    act_status = tl.actual_status_senitron
    sen_item = tl.senitron_item
    zoho_item = tl.zoho_item

    return {
        "itemNumber": tl.item_number,

        "previousStockOnHand": _to_int(tl.previous_stock_on_hand),
        "datePreviousStockOnHand": _iso(tl.date_previous_stock_on_hand),

        "actualStockOnHand": _to_int(tl.actual_stock_on_hand),
        "dateActualStockOnHand": _iso(tl.date_actual_stock_on_hand),

        "previousStatusZoho": tl.previous_status_zoho,
        "datePreviousStatusZoho": _iso(tl.date_previous_status_zoho),

        "actualStatusZoho": tl.actual_status_zoho,
        "dateActualStatusZoho": _iso(tl.date_actual_status_zoho),

        "previousQuantity": _to_int(tl.previous_quantity),
        "datePreviousQuantity": _iso(tl.date_previous_quantity),

        "actualQuantity": _to_int(tl.actual_quantity),
        "dateActualQuantity": _iso(tl.date_actual_quantity),

        "previousStatusSenitron": (
            {
                "senitronId": _to_int(prev_status.senitron_id),
                "name": prev_status.name,
            } if prev_status else None
        ),
        "datePreviousStatusSenitron": _iso(tl.date_previous_status_senitron),

        "actualStatusSenitron": (
            {
                "senitronId": _to_int(act_status.senitron_id),
                "name": act_status.name,
            } if act_status else None
        ),
        "dateActualStatusSenitron": _iso(tl.date_actual_status_senitron),

        "senitronItem": (
            {
                "itemNumber": sen_item.item_number,
                "tagsCount": sen_item.tags_count,
                "qty": sen_item.qty,
            } if sen_item else None
        ),
        "zohoItem": (
            {
                "itemId": zoho_item.item_id,
                "name": zoho_item.name,
                "status": zoho_item.status,
                "stockOnHand": zoho_item.stock_on_hand,
                "availableStock": zoho_item.available_stock,
                "actualAvailableStock": zoho_item.actual_available_stock,
            } if zoho_item else None
        ),

        "text": tl.text,
    }


# ========== SenitronItemAssetLogs ==========
def _senitron_item_asset_log_to_message_dict(lg) -> Dict[str, Any]:
    return {
        "senitronId": _to_int(lg.senitron_id),
        "serialNumber": lg.serial_number,
        "itemNumber": lg.item_number,
        "altSerial": lg.alt_serial,
        "lastSeen": _iso(lg.last_seen),
        "lastZone": lg.last_zone,
        "createdAt": _iso(lg.created_at),
        "updatedAt": _iso(lg.updated_at),
        "epc": lg.epc,
        "lastStatusId": _to_int(lg.last_status_id),
        "lastStatusName": lg.last_status_name,
        "currentStatusId": _to_int(lg.current_status_id),
        "currentStatusName": lg.current_status_name,
        "user": lg.user,
        "reason": lg.reason,
        "createdTime": _iso(lg.created_time),
    }


# ========== Notification ==========
def _notification_to_message_dict(n) -> Dict[str, Any]:
    return {
        "module": n.module,
        "info": n.info,
        "type": n.type,
        "createdAt": _iso(n.created_at),
        "updatedAt": _iso(n.updated_at),
    }


# ========== NotificationUser ==========
def _notification_user_to_message_dict(nu) -> Dict[str, Any]:
    user = getattr(nu, "user", None)
    notif = getattr(nu, "notification", None)

    return {
        "id": nu.id,
        "username": nu.username,
        "user": (
            {
                "username": user.username,
                "email": user.email,
                "isActive": bool(user.is_active),
                "isStaff": bool(user.is_staff),
                "dateJoined": _iso(getattr(user, "date_joined", None)),
                "lastLogin": _iso(getattr(user, "last_login", None)),
            } if user else None
        ),
        "notification": (
            _notification_to_message_dict(notif) if notif else None
        ),
        "read": bool(nu.read),
        "createdAt": _iso(nu.created_at),
        "updatedAt": _iso(nu.updated_at),
    }
