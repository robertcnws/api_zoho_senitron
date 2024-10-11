# Generated by Django 5.0.6 on 2024-10-11 13:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_zoho', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ZohoInventoryItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group_id', models.BigIntegerField()),
                ('group_name', models.CharField(max_length=255)),
                ('item_id', models.BigIntegerField()),
                ('name', models.CharField(max_length=255)),
                ('status', models.CharField(max_length=50)),
                ('source', models.CharField(max_length=255)),
                ('is_linked_with_zohocrm', models.BooleanField()),
                ('item_type', models.CharField(max_length=50)),
                ('description', models.TextField(blank=True, null=True)),
                ('rate', models.DecimalField(decimal_places=2, max_digits=10)),
                ('is_taxable', models.BooleanField()),
                ('tax_id', models.BigIntegerField(blank=True, null=True)),
                ('tax_name', models.CharField(blank=True, max_length=255, null=True)),
                ('tax_percentage', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('purchase_description', models.TextField(blank=True, null=True)),
                ('purchase_rate', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('is_combo_product', models.BooleanField()),
                ('product_type', models.CharField(max_length=50)),
                ('attribute_id1', models.BigIntegerField(blank=True, null=True)),
                ('attribute_name1', models.CharField(blank=True, max_length=255, null=True)),
                ('reorder_level', models.IntegerField(blank=True, null=True)),
                ('stock_on_hand', models.IntegerField()),
                ('available_stock', models.IntegerField()),
                ('actual_available_stock', models.IntegerField()),
                ('sku', models.CharField(blank=True, max_length=255, null=True)),
                ('upc', models.BigIntegerField(blank=True, null=True)),
                ('ean', models.BigIntegerField(blank=True, null=True)),
                ('isbn', models.BigIntegerField(blank=True, null=True)),
                ('part_number', models.BigIntegerField(blank=True, null=True)),
                ('attribute_option_id1', models.BigIntegerField(blank=True, null=True)),
                ('attribute_option_name1', models.CharField(blank=True, max_length=255, null=True)),
                ('image_name', models.CharField(blank=True, max_length=255, null=True)),
                ('image_type', models.CharField(blank=True, max_length=50, null=True)),
                ('created_time', models.DateField()),
                ('last_modified_time', models.DateField()),
                ('hsn_or_sac', models.BigIntegerField(blank=True, null=True)),
                ('sat_item_key_code', models.CharField(blank=True, max_length=255, null=True)),
                ('unitkey_code', models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ZohoInventoryItemCustomField',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customfield_id', models.CharField(max_length=255)),
                ('value', models.CharField(max_length=255)),
                ('inventory_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='custom_fields', to='api_zoho.zohoinventoryitem')),
            ],
        ),
    ]
