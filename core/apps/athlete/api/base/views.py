from datetime import date

from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.apps.common.date_time_utils import convert_str_date_time_to_date_time_obj
from core.apps.common.utils import make_context
from core.apps.evaluation.daily_evaluation.services import UserDailyEvaluation
from core.apps.notification.api.base.serializers import UserNotificationSerializer
from core.apps.notification.services import get_user_notification
from core.apps.plan.services import PlanService
from core.apps.user_auth.models import UserAuthModel

from ...services import AthleteService, CoachService
from .schema import AthleteInfoApiSchemaView, AthleteOverviewApiSchemaView


class AthleteInfoApiView(APIView):
    @swagger_auto_schema(
        request_body=AthleteInfoApiSchemaView.request_schema,
        responses=AthleteInfoApiSchemaView.responses,
    )
    def post(self, request, id):
        coach_api_secret_key = request.data.get("coach_api_secret_key")

        if coach_api_secret_key != settings.COACH_SERVICE_SECRET_KEY:
            return (
                Response(make_context(True, "Did not match secret key", None)),
                status.HTTP_404_NOT_FOUND,
            )

        athlete_info = AthleteService.get_athlete_info(id)
        return Response(
            make_context(False, "Athlete info returned successfully", athlete_info)
        )


class CoachInfoApiView(APIView):
    def post(self, request, id):
        coach_api_secret_key = request.data.get("coach_api_secret_key")

        if coach_api_secret_key != settings.COACH_SERVICE_SECRET_KEY:
            return Response(make_context(True, "Did not match secret key", None))

        coach_info = CoachService.get_coach_info(id)
        return Response(
            make_context(False, "Coach info returned successfully", coach_info)
        )


class AthleteOverviewApiView(APIView):
    @swagger_auto_schema(
        request_body=AthleteOverviewApiSchemaView.request_schema,
        responses=AthleteOverviewApiSchemaView.responses,
    )
    def post(self, request, id):
        coach_api_secret_key = request.data.get("coach_api_secret_key")

        if coach_api_secret_key != settings.COACH_SERVICE_SECRET_KEY:
            return Response(make_context(True, "Did not match secret key", None))

        athlete_overview = AthleteService.get_athlete_overview(id)
        return Response(
            make_context(False, "Athlete info returned successfully", athlete_overview)
        )


"""This API view is for coach portal, We need to think a better way not duplicating code
 that is already using in the core but it's done now because there is no access token of athlete
 to coach. that's why it needs to be done in another view class"""


class AthleteTodayFocusAPIView(generics.GenericAPIView):
    serializer_class = UserNotificationSerializer

    def post(self, request, user_id):
        coach_api_secret_key = request.data.get("coach_api_secret_key")

        if coach_api_secret_key != settings.COACH_SERVICE_SECRET_KEY:
            return Response(make_context(True, "Did not match secret key", None))

        user = UserAuthModel.objects.filter(pk=user_id, is_active=True).first()
        error, msg, data = get_user_notification(user)

        return Response(make_context(error, msg, data))


class AthleteCalendarApiView(APIView):
    def post(self, request, user_id, year, month):
        coach_api_secret_key = request.data.get("coach_api_secret_key")

        if coach_api_secret_key != settings.COACH_SERVICE_SECRET_KEY:
            return Response(make_context(True, "Did not match secret key", None))

        user = UserAuthModel.objects.filter(pk=user_id, is_active=True).first()

        month_plan_dict_list = PlanService.get_my_month_plan_details(user, year, month)
        return Response(
            make_context(
                False, "Month Plan returned successfully.", month_plan_dict_list
            )
        )


class AthleteDailyPrsGraphApiView(APIView):
    def post(self, request, user_id):
        coach_api_secret_key = request.data.get("coach_api_secret_key")

        if coach_api_secret_key != settings.COACH_SERVICE_SECRET_KEY:
            return Response(make_context(True, "Did not match secret key", None))

        user = UserAuthModel.objects.filter(pk=user_id, is_active=True).first()

        daily_prs_dict = UserDailyEvaluation.get_daily_prs(user, date.today())

        return Response(
            make_context(False, "Daily PRS returned successfully", daily_prs_dict)
        )


class AthleteLoadGraphApiView(APIView):
    def post(self, request, user_id):
        coach_api_secret_key = request.data.get("coach_api_secret_key")

        if coach_api_secret_key != settings.COACH_SERVICE_SECRET_KEY:
            return Response(make_context(True, "Did not match secret key", None))

        user = UserAuthModel.objects.filter(pk=user_id, is_active=True).first()
        load_graph_dict = UserDailyEvaluation.get_load_graph_data(user)

        return Response(
            make_context(
                False, "Load graph data returned successfully", load_graph_dict
            )
        )


class AthleteRecoveryGraphApiView(APIView):
    def post(self, request, user_id):
        coach_api_secret_key = request.data.get("coach_api_secret_key")

        if coach_api_secret_key != settings.COACH_SERVICE_SECRET_KEY:
            return Response(make_context(True, "Did not match secret key", None))

        user = UserAuthModel.objects.filter(pk=user_id, is_active=True).first()
        seven_days_ri_dict = UserDailyEvaluation.get_last_seven_days_recovery_index(
            user, date.today()
        )

        return Response(
            make_context(
                False,
                "Last Seven Days recovery Index data returned successfully",
                seven_days_ri_dict,
            )
        )


class AthleteSqsGraphApiView(APIView):
    def post(self, request, user_id):
        coach_api_secret_key = request.data.get("coach_api_secret_key")

        if coach_api_secret_key != settings.COACH_SERVICE_SECRET_KEY:
            return Response(make_context(True, "Did not match secret key", None))

        user = UserAuthModel.objects.filter(pk=user_id, is_active=True).first()
        seven_days_sqs_dict = UserDailyEvaluation.get_last_seven_days_sqs(
            user, date.today()
        )

        return Response(
            make_context(
                False,
                "Last Seven Days sqs data returned successfully",
                seven_days_sqs_dict,
            )
        )


class SessionDetailsApiView(APIView):
    def post(self, request, user_id, session_id):
        coach_api_secret_key = request.data.get("coach_api_secret_key")

        if coach_api_secret_key != settings.COACH_SERVICE_SECRET_KEY:
            return Response(make_context(True, "Did not match secret key", None))
        # user = UserAuthModel.objects.filter(pk=user_id, is_active=True).first()

        # commenting codes as we have already moves to the 2nd version of it.
        # Refactor it accordingly
        # session_details_data = SessionService.get_session_details_services(
        #     user, session_id
        # )
        session_details_data = None
        if session_details_data is None:
            return Response(make_context(True, "No session found for this id", None))
        return Response(
            make_context(False, "Session retrieved successfully.", session_details_data)
        )


class AthleteSpecificDateBaselineFitness(APIView):
    def post(self, request, user_id):
        dakghor_api_secret_key = request.data.get("dakghor_api_secret_key")

        if dakghor_api_secret_key != settings.DAKGHOR_API_SECRET_KEY:
            return Response(make_context(True, "Did not match secret key", None))

        activity_datetime_str = request.data.get("activity_datetime")
        activity_datetime = convert_str_date_time_to_date_time_obj(
            activity_datetime_str
        )
        baseline_fitness_info = AthleteService.get_athlete_baseline_fitness(
            user_id, activity_datetime
        )

        return Response(
            make_context(
                False,
                "Athlete baseline fitness returned successfully",
                baseline_fitness_info,
            )
        )


class AthleteFileProcessInfo(APIView):
    def post(self, request, user_id):
        dakghor_api_secret_key = request.data.get("dakghor_api_secret_key")

        if dakghor_api_secret_key != settings.DAKGHOR_API_SECRET_KEY:
            return Response(make_context(True, "Did not match secret key", None))

        activity_datetime_str = request.data.get("activity_datetime")
        activity_datetime = convert_str_date_time_to_date_time_obj(
            activity_datetime_str
        )
        file_process_info = AthleteService.get_athlete_file_process_info(
            user_id, activity_datetime
        )

        return Response(
            make_context(
                False,
                "Athlete baseline fitness returned successfully",
                file_process_info,
            )
        )


class AthleteFileProcessInfoList(APIView):
    def get(self, request, user_id):
        dakghor_api_secret_key = request.data.get("dakghor_api_secret_key")

        if dakghor_api_secret_key != settings.DAKGHOR_API_SECRET_KEY:
            return Response(make_context(True, "Did not match secret key", None))

        file_process_info_list = AthleteService.get_athlete_file_process_info_list(
            user_id
        )

        return Response(
            make_context(
                False,
                "Athlete baseline fitness list returned successfully",
                file_process_info_list,
            )
        )
