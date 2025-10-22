from celery import shared_task, chain
from api_zoho.tasks import (
    task_force_rollback_manual_update,
    task_load_inventory_items,
    task_load_inventory_shipments
)
from api_senitron.tasks import (
    task_load_senitron_inventory_item_assets,
    task_load_senitron_inventory_item_assets_logs
)

# @shared_task
# def task_sequence_2_min():
#     task_force_rollback_manual_update.delay()

@shared_task
def task_sequence_45_min():
    workflow = chain(
        # task_load_inventory_items.si(),
        task_load_senitron_inventory_item_assets.si(),
        task_load_senitron_inventory_item_assets_logs.si(),
        # task_load_inventory_shipments.si()
    )
    workflow.apply_async()
