# utils/graphql_perf.py
from typing import Iterable, List, Type
from django.db.models import QuerySet, Model

def fetch_all_streamed(qs: QuerySet, chunk_size: int = 2000) -> List[Model]:
    out: List[Model] = []
    for obj in qs.iterator(chunk_size=chunk_size):
        out.append(obj)
    return out
