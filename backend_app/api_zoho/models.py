from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


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
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username
    

class ZohoInventoryItem(models.Model):
    group_id = models.BigIntegerField()
    group_name = models.CharField(max_length=255)
    item_id = models.BigIntegerField()
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
    created_time = models.DateField()
    last_modified_time = models.DateField()
    hsn_or_sac = models.BigIntegerField(null=True, blank=True)
    sat_item_key_code = models.CharField(max_length=255, null=True, blank=True)
    unitkey_code = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name
    

class ZohoInventorySalesOrder(models.Model):
    salesorder_id = models.CharField(max_length=255, unique=True)
    documents = models.JSONField(null=True, blank=True)
    zcrm_potential_id = models.CharField(max_length=255, null=True, blank=True)
    zcrm_potential_name = models.CharField(max_length=255, null=True, blank=True)
    salesorder_number = models.CharField(max_length=255)
    date = models.DateField(null=True, blank=True)
    offline_created_date_with_time = models.DateTimeField(null=True, blank=True)
    tracking_url = models.URLField(null=True, blank=True)
    has_discount = models.BooleanField(default=False)
    status = models.CharField(max_length=100)
    color_code = models.CharField(max_length=7, null=True, blank=True)  # Assuming hex color code
    current_sub_status_id = models.CharField(max_length=255, null=True, blank=True)
    current_sub_status = models.CharField(max_length=255, null=True, blank=True)
    sub_statuses = models.JSONField(null=True, blank=True)
    order_sub_status_id = models.CharField(max_length=255, null=True, blank=True)
    invoiced_sub_status_id = models.CharField(max_length=255, null=True, blank=True)
    shipped_sub_status_id = models.CharField(max_length=255, null=True, blank=True)
    order_sub_status = models.CharField(max_length=255, null=True, blank=True)
    invoiced_sub_status = models.CharField(max_length=255, null=True, blank=True)
    shipped_sub_status = models.CharField(max_length=255, null=True, blank=True)
    shipment_date = models.DateField(null=True, blank=True)
    reference_number = models.CharField(max_length=255, null=True, blank=True)
    customer_id = models.CharField(max_length=255)
    customer_name = models.CharField(max_length=255)
    contact_persons = models.JSONField(null=True, blank=True)
    contact_persons_associated = models.JSONField(null=True, blank=True)
    contact_person_details = models.JSONField(null=True, blank=True)
    source = models.CharField(max_length=255, null=True, blank=True)
    contact_category = models.CharField(max_length=255, null=True, blank=True)
    is_taxable = models.BooleanField(default=False)
    tax_id = models.CharField(max_length=255, null=True, blank=True)
    tax_name = models.CharField(max_length=255, null=True, blank=True)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    has_shipping_address = models.BooleanField(default=False)
    currency_id = models.CharField(max_length=255)
    currency_code = models.CharField(max_length=10)
    currency_symbol = models.CharField(max_length=10)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    is_discount_before_tax = models.BooleanField(default=False)
    discount_type = models.CharField(max_length=50, null=True, blank=True)
    estimate_id = models.CharField(max_length=255, null=True, blank=True)
    delivery_method = models.CharField(max_length=255, null=True, blank=True)
    delivery_method_id = models.CharField(max_length=255, null=True, blank=True)
    is_inclusive_tax = models.BooleanField(default=False)
    tax_rounding = models.CharField(max_length=50, null=True, blank=True)
    tax_override_preference = models.CharField(max_length=50, null=True, blank=True)
    order_status = models.CharField(max_length=100)
    invoiced_status = models.CharField(max_length=100, null=True, blank=True)
    paid_status = models.CharField(max_length=100, null=True, blank=True)
    shipped_status = models.CharField(max_length=100, null=True, blank=True)
    sales_channel = models.CharField(max_length=255, null=True, blank=True)
    sales_channel_formatted = models.CharField(max_length=255, null=True, blank=True)
    account_identifier = models.CharField(max_length=255, null=True, blank=True)
    integration_id = models.CharField(max_length=255, null=True, blank=True)
    is_dropshipped = models.BooleanField(default=False)
    is_backordered = models.BooleanField(default=False)
    is_manually_fulfilled = models.BooleanField(default=False)
    can_manually_fulfill = models.BooleanField(default=False)
    has_qty_cancelled = models.BooleanField(default=False)
    shipping_details = models.JSONField(null=True, blank=True)
    created_by_email = models.EmailField(null=True, blank=True)
    created_by_name = models.CharField(max_length=255, null=True, blank=True)
    total_quantity = models.IntegerField()
    line_items = models.JSONField(null=True, blank=True)
    is_advanced_tracking_missing = models.BooleanField(default=False)
    entity_tags = models.JSONField(null=True, blank=True)
    submitter_id = models.CharField(max_length=255, null=True, blank=True)
    approver_id = models.CharField(max_length=255, null=True, blank=True)
    submitted_date = models.DateTimeField(null=True, blank=True)
    submitted_by = models.CharField(max_length=255, null=True, blank=True)
    submitted_by_name = models.CharField(max_length=255, null=True, blank=True)
    submitted_by_email = models.EmailField(null=True, blank=True)
    submitted_by_photo_url = models.URLField(null=True, blank=True)
    order_sub_statuses = models.JSONField(null=True, blank=True)
    invoice_sub_statuses = models.JSONField(null=True, blank=True)
    shipment_sub_statuses = models.JSONField(null=True, blank=True)
    price_precision = models.IntegerField(null=True, blank=True)
    is_emailed = models.BooleanField(default=False)
    has_unconfirmed_line_item = models.BooleanField(default=False)
    picklists = models.JSONField(null=True, blank=True)
    warehouses = models.JSONField(null=True, blank=True)
    billing_address_id = models.CharField(max_length=255, null=True, blank=True)
    billing_address = models.JSONField(null=True, blank=True)
    shipping_address_id = models.CharField(max_length=255, null=True, blank=True)
    shipping_address = models.JSONField(null=True, blank=True)
    is_test_order = models.BooleanField(default=False)
    notes = models.TextField(null=True, blank=True)
    terms = models.TextField(null=True, blank=True)
    payment_terms = models.CharField(max_length=255, null=True, blank=True)
    payment_terms_label = models.CharField(max_length=255, null=True, blank=True)
    custom_fields = models.JSONField(null=True, blank=True)
    template_id = models.CharField(max_length=255, null=True, blank=True)
    template_name = models.CharField(max_length=255, null=True, blank=True)
    created_time = models.DateTimeField(null=True, blank=True)
    last_modified_time = models.DateTimeField(null=True, blank=True)
    created_by_id = models.CharField(max_length=255, null=True, blank=True)
    created_date = models.DateField(null=True, blank=True)
    last_modified_by_id = models.CharField(max_length=255, null=True, blank=True)
    attachment_name = models.CharField(max_length=255, null=True, blank=True)
    can_send_in_mail = models.BooleanField(default=False)
    salesperson_id = models.CharField(max_length=255, null=True, blank=True)
    salesperson_name = models.CharField(max_length=255, null=True, blank=True)
    merchant_id = models.CharField(max_length=255, null=True, blank=True)
    merchant_name = models.CharField(max_length=255, null=True, blank=True)
    pickup_location_id = models.CharField(max_length=255, null=True, blank=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    shipping_charge = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Zoho Inventory Sales Order'
        verbose_name_plural = 'Zoho Inventory Sales Orders'

