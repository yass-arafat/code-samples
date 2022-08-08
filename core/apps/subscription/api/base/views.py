from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from core.apps.common.utils import (
    get_user_from_session_destroy_session_variable,
    make_context,
    treasury_create_subscription,
    treasury_sync_subscription,
)
from core.apps.subscription.api.base.schema import (
    SubscriptionCreateAPISchemaView,
    SubscriptionSyncAPISchemaView,
)


class SubscriptionCreateAPIView(APIView):
    @swagger_auto_schema(
        responses=SubscriptionCreateAPISchemaView.responses,
    )
    def post(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        response = treasury_create_subscription(user_code=str(user.code))
        return Response(
            make_context(
                error=response.json()["error"],
                message=response.json()["message"],
                data=response.json()["data"],
            )
        )


class SubscriptionSyncAPIView(APIView):
    @swagger_auto_schema(
        request_body=SubscriptionSyncAPISchemaView.request_schema,
        responses=SubscriptionSyncAPISchemaView.responses,
    )
    def post(self, request):
        user = get_user_from_session_destroy_session_variable(request)
        response = treasury_sync_subscription(
            user_code=str(user.code),
            app_user_id=user.email,
            invoice_code=request.data["invoice_code"],
        )
        return Response(
            make_context(
                error=response.json()["error"],
                message=response.json()["message"],
                data=response.json()["data"],
            )
        )
