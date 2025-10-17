def _shipment_to_message_dict(s) -> dict:
    f = lambda x: float(x) if x is not None else None
    iso = lambda d: d.isoformat() if d else None

    return {
        "shipmentId": s.shipment_id,
        "salesorderId": s.salesorder_id,
        "salesorderNumber": s.salesorder_number,
        "salesorderDate": iso(s.salesorder_date),
        "salesorderFulfilmentStatus": s.salesorder_fulfilment_status,
        "salesChannel": s.sales_channel,
        "salesChannelFormatted": s.sales_channel_formatted,
        "shipmentNumber": s.shipment_number,
        "date": iso(s.date),
        "shipmentStatus": s.shipment_status,
        "shipmentSubStatus": s.shipment_sub_status,
        "status": s.status,
        "detailedStatus": s.detailed_status,
        "statusMessage": s.status_message,
        "carrier": s.carrier,
        "trackingCarrierCode": s.tracking_carrier_code,
        "service": s.service,
        "deliveryDays": s.delivery_days,
        "sourceId": s.source_id,
        "labelFormat": s.label_format,
        "sourceName": s.source_name,
        "deliveryGuarantee": bool(s.delivery_guarantee),
        "referenceNumber": s.reference_number,
        "customerId": s.customer_id,
        "customerName": s.customer_name,
        "isTaxable": bool(s.is_taxable),
        "taxId": s.tax_id,
        "taxName": s.tax_name,
        "taxPercentage": f(s.tax_percentage),
        "currencyId": s.currency_id,
        "currencyCode": s.currency_code,
        "currencySymbol": s.currency_symbol,
        "exchangeRate": f(s.exchange_rate),
        "discount": f(s.discount),
        "isDiscountBeforeTax": bool(s.is_discount_before_tax),
        "discountType": s.discount_type,
        "estimateId": s.estimate_id,
        "deliveryMethod": s.delivery_method,
        "deliveryMethodId": s.delivery_method_id,
        "trackingNumber": s.tracking_number,
        "trackingLink": s.tracking_link or None,
        "lastTrackingUpdateDate": s.last_tracking_update_date,
        "expectedDeliveryDate": s.expected_delivery_date,
        "shipmentDeliveredDate": s.shipment_delivered_date,
        "shipmentType": s.shipment_type,
        "isCarrierShipment": bool(s.is_carrier_shipment),
        "isTrackingEnabled": bool(s.is_tracking_enabled),
        "isFormsAvailable": bool(s.is_forms_available),
        "isEmailNotificationEnabled": bool(s.is_email_notification_enabled),
        "shippingCharge": f(s.shipping_charge),
        "subTotal": f(s.sub_total),
        "taxTotal": f(s.tax_total),
        "total": f(s.total),
        "pricePrecision": s.price_precision,
        "isEmailed": bool(s.is_emailed),
        "notes": s.notes,
        "templateId": s.template_id,
        "templateName": s.template_name,
        "templateType": s.template_type,
        "createdTime": iso(s.created_time),
        "lastModifiedTime": iso(s.last_modified_time),
        "associatedPackagesCount": s.associated_packages_count,
        "createdById": s.created_by_id,
        "lastModifiedById": s.last_modified_by_id,

        # JSON fields (ya son serializables)
        "contactPersons": s.contact_persons,
        "invoices": s.invoices,
        "lineItems": s.line_items,
        "packages": s.packages,
        "billingAddress": s.billing_address,
        "shippingAddress": s.shipping_address,
        "customFields": s.custom_fields,
        "customFieldHash": s.custom_field_hash,
        "documents": s.documents,
        "taxes": s.taxes,
        "trackingStatuses": s.tracking_statuses,
        "multipieceShipments": s.multipiece_shipments,
    }
    

def _inventory_item_to_message_dict(it) -> dict:
    to_float = lambda v: float(v) if v is not None else None
    iso = lambda dt: dt.isoformat() if dt else None

    return {
        "groupId": it.group_id,
        "groupName": it.group_name,
        "itemId": it.item_id,
        "name": it.name,
        "status": it.status,
        "source": it.source,
        "isLinkedWithZohocrm": bool(it.is_linked_with_zohocrm),
        "itemType": it.item_type,
        "description": it.description,
        "rate": to_float(it.rate),
        "isTaxable": bool(it.is_taxable),
        "taxId": it.tax_id,
        "taxName": it.tax_name,
        "taxPercentage": to_float(it.tax_percentage),
        "purchaseDescription": it.purchase_description,
        "purchaseRate": to_float(it.purchase_rate),
        "isComboProduct": bool(it.is_combo_product),
        "productType": it.product_type,
        "attributeId1": it.attribute_id1,
        "attributeName1": it.attribute_name1,
        "reorderLevel": it.reorder_level,
        "stockOnHand": it.stock_on_hand,
        "availableStock": it.available_stock,
        "actualAvailableStock": it.actual_available_stock,
        "sku": it.sku,
        "upc": it.upc,
        "ean": it.ean,
        "isbn": it.isbn,
        "partNumber": it.part_number,
        "attributeOptionId1": it.attribute_option_id1,
        "attributeOptionName1": it.attribute_option_name1,
        "imageName": it.image_name,
        "imageType": it.image_type,
        "createdTime": iso(it.created_time),
        "lastModifiedTime": iso(it.last_modified_time),
        "hsnOrSac": it.hsn_or_sac,
        "satItemKeyCode": it.sat_item_key_code,
        "unitkeyCode": it.unitkey_code,
        "syncedWithSenitron": bool(it.synced_with_senitron),
        "ignoreErrors": bool(it.ignore_errors),
    }
    

def _sales_order_to_message_dict(so) -> dict:
    iso = lambda dt: dt.isoformat() if dt else None

    return {
        "salesorderId": so.salesorder_id,
        "salesorderNumber": so.salesorder_number,
        "date": iso(so.date),
        "status": so.status,
        "customerId": so.customer_id,
        "customerName": so.customer_name,
        "isTaxable": bool(so.is_taxable),
        "taxId": so.tax_id,
        "taxName": so.tax_name,
        "taxPercentage": so.tax_percentage if so.tax_percentage is not None else None,
        "currencyId": so.currency_id,
        "currencyCode": so.currency_code,
        "currencySymbol": so.currency_symbol,
        "exchangeRate": so.exchange_rate if so.exchange_rate is not None else None,
        "deliveryMethod": so.delivery_method,
        "totalQuantity": so.total_quantity if so.total_quantity is not None else None,
        "subTotal": so.sub_total if so.sub_total is not None else None,
        "taxTotal": so.tax_total if so.tax_total is not None else None,
        "total": so.total if so.total is not None else None,
        "createdByEmail": so.created_by_email,
        "createdByName": so.created_by_name,
        "salespersonId": so.salesperson_id,
        "salespersonName": so.salesperson_name,
        "isTestOrder": bool(so.is_test_order),
        "notes": so.notes,
        "paymentTerms": so.payment_terms,
        "paymentTermsLabel": so.payment_terms_label,

        # JSON fields (ya serializables)
        "lineItems": so.line_items,
        "shippingAddress": so.shipping_address,
        "billingAddress": so.billing_address,
        "warehouses": so.warehouses,
        "customFields": so.custom_fields,
        "orderSubStatuses": so.order_sub_statuses,
        "shipmentSubStatuses": so.shipment_sub_statuses,

        "createdTime": iso(so.created_time),
        "lastModifiedTime": iso(so.last_modified_time),
    }
    
def _sku_track_info_to_message_dict(sti) -> dict:
    iso = lambda dt: dt.isoformat() if dt else None

    return {
        "id": sti.id,
        "skuTracked": sti.sku_tracked,
        "skuMatched": sti.sku_matched,
        "skuMissing": sti.sku_missing,
        "skuExcess": sti.sku_excess,
        "date": iso(sti.date),
    }
    

def _package_to_message_dict(p) -> dict:
    to_float = lambda v: float(v) if v is not None else None
    iso = lambda d: d.isoformat() if d else None

    return {
        "packageId": p.package_id,
        "salesorderId": p.salesorder_id,
        "salesorderNumber": p.salesorder_number,
        "salesorderDate": iso(p.salesorder_date),

        "salesChannel": p.sales_channel,
        "salesChannelFormatted": p.sales_channel_formatted,
        "salesorderFulfilmentStatus": p.salesorder_fulfilment_status,

        "shipmentId": p.shipment_id,
        "shipmentNumber": p.shipment_number,
        "shipmentOrder": p.shipment_order,                 # JSON 

        "packageNumber": p.package_number,
        "date": iso(p.date),
        "shippingDate": iso(p.shipping_date),

        "deliveryMethod": p.delivery_method,
        "deliveryMethodId": p.delivery_method_id,

        "trackingNumber": p.tracking_number,
        "trackingLink": p.tracking_link or None,

        "expectedDeliveryDate": p.expected_delivery_date,
        "shipmentDeliveredDate": p.shipment_delivered_date,

        "status": p.status,
        "detailedStatus": p.detailed_status,
        "statusMessage": p.status_message,

        "carrier": p.carrier,
        "service": p.service,
        "deliveryDays": p.delivery_days,
        "deliveryGuarantee": bool(p.delivery_guarantee),

        "totalQuantity": to_float(p.total_quantity),

        "customerId": p.customer_id,
        "customerName": p.customer_name,
        "email": p.email,
        "phone": p.phone,
        "mobile": p.mobile,

        "contactPersons": p.contact_persons,               # JSON
        "createdById": p.created_by_id,
        "lastModifiedById": p.last_modified_by_id,

        "createdTime": iso(p.created_time),
        "lastModifiedTime": iso(p.last_modified_time),

        "notes": p.notes,
        "terms": p.terms,
        "isEmailed": bool(p.is_emailed),
        "isAdvancedTrackingMissing": bool(p.is_advanced_tracking_missing),

        "lineItems": p.line_items,                         # JSON
        "customFields": p.custom_fields,
        "customFieldHash": p.custom_field_hash,
        "shipmentorderCustomFields": p.shipmentorder_custom_fields,
        "billingAddress": p.billing_address,
        "shippingAddress": p.shipping_address,
        "picklists": p.picklists,

        "templateId": p.template_id,
        "templateName": p.template_name,
        "templateType": p.template_type,
        
        "zohoShipmentId": getattr(p.zoho_shipment, "shipment_id", None),
    }
    

def _item_assets_track_to_message_dict(t) -> dict:
    iso = lambda dt: dt.isoformat() if dt else None

    return {
        "id": t.id,
        "itemId": t.item_id,
        "sku": t.sku,
        "assets": t.assets,            
        "createdTime": iso(t.created_time),
    }
    
    
def _jobs_updating_times_to_message_dict(j) -> dict:
    iso = lambda dt: dt.isoformat() if dt else None
    return {
        "id": j.id,
        "lastUpdated": iso(j.last_updated),
    }
    

def _manual_updating_jobs_to_message_dict(m) -> dict:
    iso = lambda dt: dt.isoformat() if dt else None
    return {
        "id": m.id,
        "isRunning": bool(m.is_running),
        "lastUpdated": iso(m.last_updated),
    }
    

def _login_user_to_message_dict(u) -> dict:
    iso = lambda dt: dt.isoformat() if dt else None

    return {
        "username": u.username,
        "firstName": u.first_name,
        "lastName": u.last_name,
        "email": u.email,
        "isStaff": bool(u.is_staff),
        "isActive": bool(u.is_active),
        "isSuperuser": bool(getattr(u, "is_superuser", False)),
        "dateJoined": iso(getattr(u, "date_joined", None)),
        "lastLogin": iso(getattr(u, "last_login", None)),
        "phoneNumber": u.phone_number,
        "country": u.country,
        "state": u.state,
        "city": u.city,
        "address": u.address,
        "zipCode": u.zip_code,
        "gender": u.gender,
    }




