from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from .services import (
    sync_inventory_items,
    sync_inventory_shipments,
)
from .views import force_rollback_manual_update
from .models import JobsUpdatingTimes

from common.sync_state import get_cursor, set_cursor, _run_lock, _release_lock, _jitter_sleep
from common.rate_limit import token_bucket, backoff
import requests

DEFAULT_SYSTEM_USERNAME = "System Job"
ZOHO_ITEMS_RATE_PER_MIN = 20
ZOHO_SHIP_RATE_PER_MIN = 12

@shared_task(bind=True, max_retries=7)
def task_load_inventory_items(self, username=DEFAULT_SYSTEM_USERNAME, force_full=False):
    if self.request.retries == 0:
        _jitter_sleep(8.0)
    lock = _run_lock("zoho:items", ttl=240)
    if lock is None:
        return
    try:
        if not token_bucket("zoho:items", rate=40, per=60):
            raise self.retry(countdown=1)
        cursor = None if force_full else get_cursor("zoho:items")
        if cursor is None:
            cursor = timezone.now() - timedelta(days=1)

        out = sync_inventory_items(updated_since=cursor, username=username)
        if out.get("changed"):
            JobsUpdatingTimes.objects.create(last_updated=timezone.now())
        if out.get("max_ts"):
            set_cursor("zoho:items", out["max_ts"])
    except requests.RequestException as e:
        raise self.retry(exc=e, countdown=backoff(self.request.retries))
    except Exception as e:
        raise self.retry(exc=e, countdown=backoff(self.request.retries))
    finally:
        _release_lock(lock)


@shared_task(bind=True, max_retries=7)
def task_load_inventory_shipments(self, username=DEFAULT_SYSTEM_USERNAME, force_full=False):
    if self.request.retries == 0:
        _jitter_sleep(12.0)
    lock = _run_lock("zoho:shipments", ttl=240)
    if lock is None:
        return
    try:
        if not token_bucket("zoho:shipments", rate=30, per=60):
            raise self.retry(countdown=1)
        cursor = None if force_full else get_cursor("zoho:shipments")
        if cursor is None:
            cursor = timezone.now() - timedelta(days=1)
        out = sync_inventory_shipments(start_date=None, end_date=None, updated_since=cursor, username=username)
        if out.get("changed"):
            JobsUpdatingTimes.objects.create(last_updated=timezone.now())
        if out.get("max_ts"):
            set_cursor("zoho:shipments", out["max_ts"])
    except requests.RequestException as e:
        raise self.retry(exc=e, countdown=backoff(self.request.retries))
    except Exception as e:
        raise self.retry(exc=e, countdown=backoff(self.request.retries))
    finally:
        _release_lock(lock)


@shared_task
def task_force_rollback_manual_update():
    force_rollback_manual_update()



# from celery import shared_task
# from datetime import datetime
# from django.http import HttpRequest
# from django.utils import timezone
# from .views import load_inventory_shipments, load_inventory_items, force_rollback_manual_update
# from .models import JobsUpdatingTimes
# import json
    
# @shared_task
# def task_load_inventory_items():
#     request = HttpRequest()
#     request.method = 'POST'
#     request.content_type = 'application/json'
#     request._body = json.dumps({}).encode('utf-8')
#     load_inventory_items(request)
    
# @shared_task
# def task_load_inventory_shipments():
#     start_date = datetime.now().strftime("%Y-%m-%d")
#     data = {'start_date': start_date}
#     request = HttpRequest()
#     request.method = 'POST'
#     request.content_type = 'application/json'
#     request._body = json.dumps(data).encode('utf-8')
#     load_inventory_shipments(request)
#     JobsUpdatingTimes.objects.create(last_updated=timezone.now())
    

# @shared_task    
# def task_force_rollback_manual_update():
#     force_rollback_manual_update()