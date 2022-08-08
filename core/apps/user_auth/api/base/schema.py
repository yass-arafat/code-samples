from drf_yasg import openapi
from drf_yasg.openapi import Schema


class LoginApiSchemaView:
    request_schema = Schema(
        title="Request data example", type=openapi.TYPE_OBJECT, properties={}
    )
