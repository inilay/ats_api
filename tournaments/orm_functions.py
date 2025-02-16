from django.db.models import JSONField
from django.db.models.aggregates import Aggregate


class JsonGroupArray(Aggregate):
    function = "JSON_GROUP_ARRAY"
    output_field = JSONField()
    allow_distinct = True
    template = "%(function)s(%(distinct)s%(expressions)s)"
