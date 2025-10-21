# models.py
from django.db import models
from django.utils import timezone
from api_zoho.models import ZohoInventoryItem, LoginUser

class SenitronItem(models.Model):
    item_number = models.CharField(max_length=255, unique=True)
    item_number_int = models.BigIntegerField(null=True, blank=True, db_index=True)
    tags_count = models.IntegerField()
    qty = models.IntegerField()
    def __str__(self):
        return self.item_number
    class Meta:
        indexes = [models.Index(fields=['item_number'])]

class SenitronStatus(models.Model):
    senitron_id = models.IntegerField(unique=True, null=True, default=None)
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name
    class Meta:
        indexes = [models.Index(fields=['name'])]

class SenitronItemAsset(models.Model):
    serial_number = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    item_number = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    alt_serial = models.CharField(max_length=50, blank=True, null=True)
    first_seen = models.DateTimeField(blank=True, null=True, db_index=True)
    last_seen = models.DateTimeField(blank=True, null=True, db_index=True)
    last_seen_antenna = models.CharField(max_length=50, blank=True, null=True)
    last_zone = models.CharField(max_length=255, blank=True, null=True)
    handheld_reader = models.CharField(max_length=255, blank=True, null=True)
    handheld_last_seen = models.DateTimeField(blank=True, null=True)
    static_zone = models.CharField(max_length=255, blank=True, null=True)
    static_zone_last_update = models.DateTimeField(blank=True, null=True)
    receiving_date = models.DateTimeField(blank=True, null=True)
    current_units = models.FloatField(default=0.0)
    storage_unit = models.FloatField(default=0.0)
    adjust_qty = models.IntegerField(default=0)
    attr1 = models.CharField(max_length=255, blank=True, null=True)
    attr2 = models.CharField(max_length=255, blank=True, null=True)
    attr3 = models.CharField(max_length=255, blank=True, null=True)
    attr4 = models.CharField(max_length=255, blank=True, null=True)
    attr5 = models.CharField(max_length=255, blank=True, null=True)
    attr6 = models.CharField(max_length=255, blank=True, null=True)
    attr7 = models.CharField(max_length=255, blank=True, null=True)
    attr8 = models.CharField(max_length=255, blank=True, null=True)
    attr9 = models.CharField(max_length=255, blank=True, null=True)
    attr10 = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True, db_index=True)
    updated_at = models.DateTimeField(blank=True, null=True, db_index=True)
    epc = models.CharField(max_length=255, null=True, blank=True)
    text3 = models.TextField(blank=True, null=True)
    status = models.ForeignKey(SenitronStatus, on_delete=models.CASCADE, null=True, related_name='status')
    senitron_item = models.ForeignKey(SenitronItem, on_delete=models.CASCADE, null=True, related_name='senitron_item')
    read = models.BooleanField(default=False, db_index=True)
    date_read = models.DateTimeField(blank=True, null=True)
    def __str__(self):
        return f"Item {self.item_number} - Serial: {self.serial_number} - EPC: {self.epc} - Status: {self.status.name} - Serial: {self.serial_number} - Last Seen: {self.last_seen}"
    class Meta:
        indexes = [models.Index(fields=['item_number', 'updated_at']), models.Index(fields=['item_number', 'last_seen'])]

class TimelineItem(models.Model):
    item_number = models.CharField(max_length=255, db_index=True)
    previous_stock_on_hand = models.IntegerField(null=True)
    date_previous_stock_on_hand = models.DateTimeField(null=True, db_index=True)
    actual_stock_on_hand = models.IntegerField(null=True)
    date_actual_stock_on_hand = models.DateTimeField(null=True, db_index=True)
    previous_status_zoho = models.CharField(max_length=255, null=True)
    date_previous_status_zoho = models.DateTimeField(null=True, db_index=True)
    actual_status_zoho = models.CharField(max_length=255, null=True)
    date_actual_status_zoho = models.DateTimeField(null=True, db_index=True)
    previous_quantity = models.IntegerField(null=True)
    date_previous_quantity = models.DateTimeField(null=True, db_index=True)
    actual_quantity = models.IntegerField(null=True)
    date_actual_quantity = models.DateTimeField(null=True, db_index=True)
    previous_status_senitron = models.ForeignKey(SenitronStatus, on_delete=models.CASCADE, null=True, related_name='previous_status_senitron')
    date_previous_status_senitron = models.DateTimeField(null=True, db_index=True)
    actual_status_senitron = models.ForeignKey(SenitronStatus, on_delete=models.CASCADE, null=True, related_name='actual_status_senitron')
    date_actual_status_senitron = models.DateTimeField(null=True, db_index=True)
    senitron_item = models.ForeignKey(SenitronItem, on_delete=models.CASCADE, null=True, related_name='timeline_senitron_item')
    zoho_item = models.ForeignKey(ZohoInventoryItem, on_delete=models.CASCADE, null=True, related_name='timeline_zoho_item')
    text = models.TextField(blank=True, null=True)
    def __str__(self):
        return f"Item {self.item_number} - {self.actual_quantity} - {self.date_actual_quantity}"
    class Meta:
        indexes = [models.Index(fields=['date_actual_stock_on_hand']), models.Index(fields=['date_actual_status_zoho']), models.Index(fields=['date_actual_quantity']), models.Index(fields=['date_actual_status_senitron'])]

class SenitronItemAssetLogs(models.Model):
    senitron_id = models.IntegerField(unique=True, null=True, default=None)
    serial_number = models.CharField(max_length=50, blank=True, null=True)
    item_number = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    alt_serial = models.CharField(max_length=50, blank=True, null=True)
    last_seen = models.DateTimeField(blank=True, null=True)
    last_zone = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    epc = models.CharField(max_length=255, null=True, blank=True)
    last_status_id = models.IntegerField(null=True)
    last_status_name = models.CharField(max_length=100, null=True)
    current_status_id = models.IntegerField(null=True)
    current_status_name = models.CharField(max_length=100, null=True)
    user = models.CharField(max_length=255, blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_time = models.DateTimeField(default=timezone.now, db_index=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['serial_number', 'current_status_id', 'current_status_name', 'last_status_id', 'last_status_name', 'updated_at'], name='unique_asset_log_combination')]
        indexes = [models.Index(fields=['item_number', 'created_time'])]
    def __str__(self):
        return f"Item {self.item_number} - Serial: {self.serial_number} - EPC: {self.epc} - Status: {self.current_status_name} - Serial: {self.serial_number} - Last Seen: {self.last_seen}"

class Notification(models.Model):
    module = models.CharField(max_length=255, db_index=True)
    info = models.TextField()
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(default=timezone.now)
    type = models.CharField(max_length=255, default='load')
    def __str__(self):
        return self.info

class NotificationUser(models.Model):
    id = models.AutoField(primary_key=True)
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    username = models.CharField(max_length=255, db_index=True)
    user = models.ForeignKey(LoginUser, on_delete=models.CASCADE, null=True)
    read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(default=timezone.now)
    def __str__(self):
        return f'{self.username} - {self.notification.info}'
