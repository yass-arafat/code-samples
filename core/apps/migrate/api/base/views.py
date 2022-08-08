from rest_framework.views import APIView

from core.apps.common.common_functions import pillar_response
from core.apps.migrate import services


class MigrateDataView(APIView):
    @pillar_response()
    def get(self, request):
        user_id = request.GET.get("user_id")
        payload = services.MigratePlannedDayService(user_id=user_id).migrate_data()
        return payload
