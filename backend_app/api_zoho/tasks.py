from celery import shared_task
from django.utils import timezone
from django.conf import settings
from datetime import timedelta

from .services_from_main_load import (
    sync_inventory_items,
    sync_inventory_shipments,
)
from .views import force_rollback_manual_update

from common.sync_state import _run_lock, _release_lock, _jitter_sleep
from common.rate_limit import token_bucket, backoff
import requests

DEFAULT_SYSTEM_USERNAME = "System Job"

# Ajusta las cuotas a tus límites reales de API
API_ITEMS_RATE_PER_MIN = 20
API_SHIP_RATE_PER_MIN = 12

def _today_ymd() -> str:
    """Devuelve la fecha actual en YYYY-MM-DD (ej. 2020-10-27)."""
    return timezone.now().date().strftime("%Y-%m-%d")


@shared_task(bind=True, max_retries=7)
def task_load_inventory_items(self, username=DEFAULT_SYSTEM_USERNAME):
    """
    Carga de ITEMS desde la nueva API.
    - Usa start_date=YYYY-MM-DD (hoy).
    - No usa cursor ni updated_since (la API ya devuelve lo necesario).
    """
    if self.request.retries == 0:
        _jitter_sleep(8.0)

    lock = _run_lock("api:items", ttl=240)
    if lock is None:
        return

    try:
        # rate-limit general para esta tarea
        if not token_bucket("api:items", rate=API_ITEMS_RATE_PER_MIN, per=60):
            raise self.retry(countdown=1)

        difference = timedelta(days=settings.DIFF_DAYS_FOR_FULL_SYNC)
        start_date = (timezone.now() - difference).date().strftime("%Y-%m-%d")
        end_date = (timezone.now()).date().strftime("%Y-%m-%d")
        out = sync_inventory_items(start_date=start_date, end_date=end_date, username=username)
        # Si quieres forzar algo adicional cuando hay cambios:
        # if out.get("changed"):
        #     JobsUpdatingTimes.objects.create(last_updated=timezone.now())

    except requests.RequestException as e:
        raise self.retry(exc=e, countdown=backoff(self.request.retries))
    except Exception as e:
        raise self.retry(exc=e, countdown=backoff(self.request.retries))
    finally:
        _release_lock(lock)


@shared_task(bind=True, max_retries=7)
def task_load_inventory_shipments(self, username=DEFAULT_SYSTEM_USERNAME):
    """
    Carga de SHIPMENTS & PACKAGES desde la nueva API.
    - Usa start_date=YYYY-MM-DD (hoy).
    - No usa cursor ni updated_since (lista ya viene completa).
    - Packages se resuelven en bulk dentro de la service.
    """
    if self.request.retries == 0:
        _jitter_sleep(12.0)

    lock = _run_lock("api:shipments", ttl=240)
    if lock is None:
        return

    try:
        if not token_bucket("api:shipments", rate=API_SHIP_RATE_PER_MIN, per=60):
            raise self.retry(countdown=1)

        difference = timedelta(days=settings.DIFF_DAYS_FOR_FULL_SYNC)
        start_date = (timezone.now() - difference).date().strftime("%Y-%m-%d")
        end_date = (timezone.now()).date().strftime("%Y-%m-%d")
        out = sync_inventory_shipments(start_date=start_date, end_date=end_date, updated_since=None, username=username)
        # if out.get("changed"):
        #     JobsUpdatingTimes.objects.create(last_updated=timezone.now())

    except requests.RequestException as e:
        raise self.retry(exc=e, countdown=backoff(self.request.retries))
    except Exception as e:
        raise self.retry(exc=e, countdown=backoff(self.request.retries))
    finally:
        _release_lock(lock)


@shared_task
def task_force_rollback_manual_update():
    force_rollback_manual_update()
