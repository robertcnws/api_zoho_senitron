from decimal import Decimal
from datetime import datetime, date

def serialize(instance):
    serialized_data = {}
    for field in instance._meta.fields:
        value = getattr(instance, field.name)
        serialized_data[field.name] = handle_special_types(value)
    return serialized_data

def handle_special_types(value):
    if isinstance(value, Decimal):
        return float(value)
    elif isinstance(value, (datetime, date)):
        return value.isoformat()
    elif isinstance(value, (list, tuple)):
        return [handle_special_types(v) for v in value]
    elif isinstance(value, dict):
        return {k: handle_special_types(v) for k, v in value.items()}
    else:
        return value