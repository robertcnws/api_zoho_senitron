# tu_app/scalars.py

import json
import graphene
from graphql.language import ast

class JSONScalar(graphene.Scalar):
    """Escalar personalizado para manejar objetos JSON."""

    @staticmethod
    def serialize(value):
        # Asegúrate de que el valor es serializable a JSON
        return value

    @staticmethod
    def parse_literal(node):
        if isinstance(node, ast.StringValue):
            try:
                return json.loads(node.value)
            except json.JSONDecodeError:
                return None
        elif isinstance(node, ast.IntValue):
            return int(node.value)
        elif isinstance(node, ast.FloatValue):
            return float(node.value)
        elif isinstance(node, ast.BooleanValue):
            return node.value
        elif isinstance(node, ast.ListValue):
            return [JSONScalar.parse_literal(value) for value in node.values]
        elif isinstance(node, ast.ObjectValue):
            return {field.name.value: JSONScalar.parse_literal(field.value) for field in node.fields}
        else:
            return None

    @staticmethod
    def parse_value(value):
        return value
