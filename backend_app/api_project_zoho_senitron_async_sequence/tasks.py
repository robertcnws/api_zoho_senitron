from celery import shared_task, chain
from api_zoho.tasks import (
    task_load_inventory_items,
    task_load_inventory_shipments
)
from api_senitron.tasks import (
    task_load_senitron_inventory_item_assets,
    task_load_senitron_inventory_item_assets_logs
)

@shared_task
def task_sequence_data_from_senitron():
    workflow = chain(
        task_load_senitron_inventory_item_assets.si(),
        task_load_senitron_inventory_item_assets_logs.si(),
    )
    workflow.apply_async()
    
@shared_task
def task_sequence_data_from_zoho():
    workflow = chain(
        task_load_inventory_items.si(),
        task_load_inventory_shipments.si()
    )
    workflow.apply_async()
