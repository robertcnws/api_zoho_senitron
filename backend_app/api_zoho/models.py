from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db.models import JSONField
from django.utils import timezone


class AppConfig(models.Model):
    id = models.AutoField(primary_key=True)
    # Zoho API connection fields
    zoho_client_id = models.CharField(max_length=255, blank=True, null=True)
    zoho_client_secret = models.CharField(max_length=255, blank=True, null=True)
    zoho_org_id = models.CharField(max_length=255, blank=True, null=True)
    zoho_redirect_uri = models.CharField(max_length=255, blank=True, null=True)
    zoho_refresh_time = models.DurationField(blank=True, null=True)
    zoho_refresh_token = models.CharField(max_length=255, blank=True, null=True)  
    zoho_connection_configured = models.BooleanField(default=False)  
    zoho_last_sync_time = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.pk and AppConfig.objects.exists():
            self.pk = AppConfig.objects.get().pk
        
        required_fields = [
            self.zoho_client_id,
            self.zoho_client_secret,
            self.zoho_org_id,
            self.zoho_redirect_uri,
        ]
        
        self.zoho_connection_configured = all(
            field is not None and field != "" for field in required_fields
        )

        super(AppConfig, self).save(*args, **kwargs)

    def __str__(self):
        return f"App Configuration for {self.zoho_org_id}"
    
    
class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(username, password, **extra_fields)

class LoginUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    zip_code = models.CharField(max_length=50, blank=True, null=True)
    gender = models.CharField(max_length=50, blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username
    

class ZohoInventoryItem(models.Model):
    group_id = models.BigIntegerField()
    group_name = models.CharField(max_length=255)
    item_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    source = models.CharField(max_length=255)
    is_linked_with_zohocrm = models.BooleanField()
    item_type = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    is_taxable = models.BooleanField()
    tax_id = models.BigIntegerField(null=True, blank=True)
    tax_name = models.CharField(max_length=255, null=True, blank=True)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    purchase_description = models.TextField(null=True, blank=True)
    purchase_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_combo_product = models.BooleanField()
    product_type = models.CharField(max_length=50)
    attribute_id1 = models.BigIntegerField(null=True, blank=True)
    attribute_name1 = models.CharField(max_length=255, null=True, blank=True)
    reorder_level = models.IntegerField(null=True, blank=True)
    stock_on_hand = models.IntegerField()
    available_stock = models.IntegerField()
    actual_available_stock = models.IntegerField()
    sku = models.CharField(max_length=255, null=True, blank=True)
    upc = models.BigIntegerField(null=True, blank=True)
    ean = models.BigIntegerField(null=True, blank=True)
    isbn = models.BigIntegerField(null=True, blank=True)
    part_number = models.BigIntegerField(null=True, blank=True)
    attribute_option_id1 = models.BigIntegerField(null=True, blank=True)
    attribute_option_name1 = models.CharField(max_length=255, null=True, blank=True)
    image_name = models.CharField(max_length=255, null=True, blank=True)
    image_type = models.CharField(max_length=50, null=True, blank=True)
    created_time = models.DateTimeField()
    last_modified_time = models.DateTimeField()
    hsn_or_sac = models.BigIntegerField(null=True, blank=True)
    sat_item_key_code = models.CharField(max_length=255, null=True, blank=True)
    unitkey_code = models.CharField(max_length=255, null=True, blank=True)
    synced_with_senitron = models.BooleanField(default=False)   
    ignore_errors = models.BooleanField(default=False) 

    def __str__(self):
        return self.name
    
    
class ZohoInventoryShipmentSalesOrder(models.Model):
    salesorder_id = models.CharField(max_length=255, unique=True)
    salesorder_number = models.CharField(max_length=255, null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=100, null=True, blank=True)
    customer_id = models.CharField(max_length=255, null=True, blank=True)
    customer_name = models.CharField(max_length=255, null=True, blank=True)
    is_taxable = models.BooleanField(default=True)
    tax_id = models.CharField(max_length=255, null=True, blank=True)
    tax_name = models.CharField(max_length=255, null=True, blank=True)
    tax_percentage = models.FloatField(null=True, blank=True)
    currency_id = models.CharField(max_length=255, null=True, blank=True)
    currency_code = models.CharField(max_length=10, null=True, blank=True)
    currency_symbol = models.CharField(max_length=5, null=True, blank=True)
    exchange_rate = models.FloatField(default=1.0, null=True, blank=True)
    delivery_method = models.CharField(max_length=255, null=True, blank=True)
    total_quantity = models.FloatField(default=0, null=True, blank=True)
    sub_total = models.FloatField(default=0, null=True, blank=True)
    tax_total = models.FloatField(default=0, null=True, blank=True)
    total = models.FloatField(default=0, null=True, blank=True)
    created_by_email = models.EmailField(null=True, blank=True)
    created_by_name = models.CharField(max_length=255, null=True, blank=True)
    salesperson_id = models.CharField(max_length=255, null=True, blank=True)
    salesperson_name = models.CharField(max_length=255, null=True, blank=True)
    is_test_order = models.BooleanField(default=False)
    notes = models.TextField(null=True, blank=True)
    payment_terms = models.IntegerField(default=0)
    payment_terms_label = models.CharField(max_length=255, null=True, blank=True)
    
    line_items = JSONField(default=list, null=True, blank=True) 
    shipping_address = JSONField(null=True, blank=True)
    billing_address = JSONField(null=True, blank=True)
    warehouses = JSONField(default=list, null=True, blank=True)
    custom_fields = JSONField(default=dict, null=True, blank=True) 
    order_sub_statuses = JSONField(default=list, null=True, blank=True)
    shipment_sub_statuses = JSONField(default=list, null=True, blank=True)
    
    created_time = models.DateTimeField(null=True, blank=True)
    last_modified_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Zoho Inventory Sales Order'
        verbose_name_plural = 'Zoho Inventory Sales Orders'

    def __str__(self):
        return f"Sales Order {self.salesorder_number} - {self.customer_name}"
    
    
class ZohoSkuTrackInfo(models.Model):
    id = models.AutoField(primary_key=True)
    sku_tracked = models.IntegerField(default=0)
    sku_matched = models.IntegerField(default=0)
    sku_missing = models.IntegerField(default=0)
    sku_excess = models.IntegerField(default=0)
    date = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"SKU Tracking Info for {self.date}"
  
    
class ZohoShipmentOrder(models.Model):
    shipment_id = models.CharField(max_length=50, primary_key=True)
    salesorder_id = models.CharField(max_length=50, blank=True, null=True)
    salesorder_number = models.CharField(max_length=50, blank=True, null=True)
    salesorder_date = models.DateField()
    salesorder_fulfilment_status = models.CharField(max_length=50, blank=True, null=True)
    sales_channel = models.CharField(max_length=50, blank=True, null=True)
    sales_channel_formatted = models.CharField(max_length=50, blank=True, null=True)
    shipment_number = models.CharField(max_length=50, blank=True, null=True)
    date = models.DateField()
    shipment_status = models.CharField(max_length=50, blank=True, null=True)
    shipment_sub_status = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    detailed_status = models.CharField(max_length=255, blank=True, null=True)
    status_message = models.CharField(max_length=255, blank=True, null=True)
    carrier = models.CharField(max_length=50, blank=True, null=True)
    tracking_carrier_code = models.CharField(max_length=50, blank=True, null=True)
    service = models.CharField(max_length=50, blank=True, null=True)
    delivery_days = models.CharField(max_length=50, blank=True, null=True)
    source_id = models.CharField(max_length=50, blank=True, null=True)
    label_format = models.CharField(max_length=50, blank=True, null=True)
    source_name = models.CharField(max_length=50, blank=True, null=True)
    delivery_guarantee = models.BooleanField()
    reference_number = models.CharField(max_length=50, blank=True, null=True)
    customer_id = models.CharField(max_length=50, blank=True, null=True)
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    is_taxable = models.BooleanField(default=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    tax_name = models.CharField(max_length=50, blank=True, null=True)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    currency_id = models.CharField(max_length=50, blank=True, null=True)
    currency_code = models.CharField(max_length=10, blank=True, null=True)
    currency_symbol = models.CharField(max_length=10, blank=True, null=True)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, default=1)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_discount_before_tax = models.BooleanField()
    discount_type = models.CharField(max_length=50, blank=True, null=True)
    estimate_id = models.CharField(max_length=50, blank=True, null=True)
    delivery_method = models.CharField(max_length=50, blank=True, null=True)
    delivery_method_id = models.CharField(max_length=50, blank=True, null=True)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    tracking_link = models.URLField(blank=True, null=True)
    last_tracking_update_date = models.CharField(max_length=100, blank=True, null=True)
    expected_delivery_date = models.CharField(max_length=100, blank=True, null=True)
    shipment_delivered_date = models.CharField(max_length=100, blank=True, null=True)
    shipment_type = models.CharField(max_length=50)
    is_carrier_shipment = models.BooleanField(default=False)
    is_tracking_enabled = models.BooleanField(default=False)
    is_forms_available = models.BooleanField(default=False)
    is_email_notification_enabled = models.BooleanField(default=False)
    shipping_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_precision = models.IntegerField(default=0)
    is_emailed = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    template_id = models.CharField(max_length=50, blank=True, null=True)
    template_name = models.CharField(max_length=50, blank=True, null=True)
    template_type = models.CharField(max_length=50, blank=True, null=True)
    created_time = models.DateTimeField(default=timezone.now)
    last_modified_time = models.DateTimeField(default=timezone.now)
    associated_packages_count = models.IntegerField(default=0)
    created_by_id = models.CharField(max_length=50, blank=True, null=True)
    last_modified_by_id = models.CharField(max_length=50, blank=True, null=True)
    
    contact_persons = models.JSONField(blank=True, null=True)
    invoices = models.JSONField(blank=True, null=True)
    line_items = models.JSONField(blank=True, null=True)
    packages = models.JSONField(blank=True, null=True)
    billing_address = models.JSONField(blank=True, null=True)
    shipping_address = models.JSONField(blank=True, null=True)
    custom_fields = models.JSONField(blank=True, null=True)
    custom_field_hash = models.JSONField(blank=True, null=True)
    documents = models.JSONField(blank=True, null=True)
    taxes = models.JSONField(blank=True, null=True)
    tracking_statuses = models.JSONField(blank=True, null=True)
    multipiece_shipments = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"ShipmentOrder {self.shipment_number}"
    

class ZohoPackage(models.Model):
    package_id = models.CharField(max_length=50, primary_key=True)
    salesorder_id = models.CharField(max_length=50, blank=True, null=True)
    salesorder_number = models.CharField(max_length=50, blank=True, null=True)
    salesorder_date = models.DateField(blank=True, null=True)
    sales_channel = models.CharField(max_length=50, blank=True, null=True)
    sales_channel_formatted = models.CharField(max_length=50, blank=True, null=True)
    salesorder_fulfilment_status = models.CharField(max_length=50, blank=True, null=True)
    shipment_id = models.CharField(max_length=50, blank=True, null=True)
    shipment_number = models.CharField(max_length=50, blank=True, null=True)
    shipment_order = models.JSONField(blank=True, null=True)
    package_number = models.CharField(max_length=50, blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    shipping_date = models.DateField(blank=True, null=True)
    delivery_method = models.CharField(max_length=50, blank=True, null=True)
    delivery_method_id = models.CharField(max_length=50, blank=True, null=True)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    tracking_link = models.URLField(blank=True, null=True)
    expected_delivery_date = models.CharField(max_length=100, blank=True, null=True)
    shipment_delivered_date = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    detailed_status = models.CharField(max_length=255, blank=True, null=True)
    status_message = models.CharField(max_length=255, blank=True, null=True)
    carrier = models.CharField(max_length=50, blank=True, null=True)
    service = models.CharField(max_length=50, blank=True, null=True)
    delivery_days = models.CharField(max_length=50, blank=True, null=True)
    delivery_guarantee = models.BooleanField(default=False)
    total_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    customer_id = models.CharField(max_length=50, blank=True, null=True)
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    contact_persons = models.JSONField(blank=True, null=True)
    created_by_id = models.CharField(max_length=50, blank=True, null=True)
    last_modified_by_id = models.CharField(max_length=50, blank=True, null=True)
    created_time = models.DateTimeField(blank=True, null=True)
    last_modified_time = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    terms = models.TextField(blank=True, null=True)
    is_emailed = models.BooleanField(default=False)
    is_advanced_tracking_missing = models.BooleanField(default=False)
    line_items = models.JSONField(blank=True, null=True)
    custom_fields = models.JSONField(blank=True, null=True)
    custom_field_hash = models.JSONField(blank=True, null=True)
    shipmentorder_custom_fields = models.JSONField(blank=True, null=True)
    billing_address = models.JSONField(blank=True, null=True)
    shipping_address = models.JSONField(blank=True, null=True)
    picklists = models.JSONField(blank=True, null=True)
    template_id = models.CharField(max_length=50, blank=True, null=True)
    template_name = models.CharField(max_length=100, blank=True, null=True)
    template_type = models.CharField(max_length=50, blank=True, null=True)
    zoho_shipment = models.ForeignKey(ZohoShipmentOrder, on_delete=models.CASCADE, blank=True, null=True)
    
    def __str__(self):
        return f"ZohoPackage {self.package_number}"
    
    
class ZohoItemAssetsTrack(models.Model):
    id = models.AutoField(primary_key=True)
    item_id = models.CharField(max_length=255, null=True, blank=True)
    sku = models.CharField(max_length=255, null=True, blank=True)
    assets = models.JSONField(default=list, null=True, blank=True)
    created_time = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"ItemAssetsTrack {self.item_id} - Created on {self.created_time}"

