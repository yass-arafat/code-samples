import logging

from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from core.apps.common.common_functions import pro_feature
from core.apps.common.utils import (
    get_user_from_session_destroy_session_variable,
    make_context,
)

from ...models import Package
from ...services import (
    KnowledgeHubViewService,
    PackageDurationService,
    PackageKnowledgeHubViewService,
    SubPackageService,
)
from .schema import PackageDurationSchemaView
from .serializers import PackageInfoSerializer, PackageSerializer

logger = logging.getLogger(__name__)


class PackageListView(APIView):
    def get(self, request):
        """Returns a list of all the active packages."""
        goal_type = request.GET.get("goal_type")
        try:
            package_objects = Package.objects.filter(
                is_active=True, goal_type=goal_type
            ).order_by("name")
            serializer = PackageSerializer(package_objects, many=True)
            package_list = serializer.data
            error = False
            msg = "Package list returned successfully"

        except Exception as e:
            msg = "Could not get any package."
            error = True
            package_list = None
            logger.exception(str(e) + msg)

        return Response(make_context(error, msg, package_list))


class PackageInfoView(APIView):
    def get(self, request, package_id):
        """Returns the information related to a specific package i.e duration of this package"""
        try:
            user = get_user_from_session_destroy_session_variable(request)
            package = Package.objects.get(is_active=True, id=package_id)
            serializer = PackageInfoSerializer(package, context={"user": user})
            package_details = serializer.data
            msg = "Package details returned successfully"
            error = False

        except Exception as e:
            msg = "Could not get package details"
            error = True
            package_details = None
            logger.exception(str(e) + msg)

        return Response(make_context(error, msg, package_details))


class SubPackageView(APIView):
    @pro_feature
    def get(self, request, package_id):
        """Returns a list of all the active sub packages of a specific package."""
        try:
            # Need to call the following function and remove user object from session,
            # unless django can't store the session in db
            get_user_from_session_destroy_session_variable(request)

            sub_packages = SubPackageService.get_sub_packages(package_id)
            msg = "Sub packages returned successfully"
            error = False

        except Exception as e:
            msg = "Could not get any sub package."
            error = True
            sub_packages = None
            logger.exception(str(e) + msg)

        return Response(make_context(error, msg, sub_packages))


class PackageDurationView(APIView):
    @swagger_auto_schema(responses=PackageDurationSchemaView.responses)
    @pro_feature
    def get(self, request, package_id, sub_package_id):
        """Returns a list of all duration for the packages"""
        try:
            # Need to call the following function and remove user object from session,
            # unless django can't store the session in db
            get_user_from_session_destroy_session_variable(request)

            package_duration = PackageDurationService.get_package_duration_list()
            msg = "Package duration returned successfully"
            error = False
        except Exception as e:
            msg = "Package duration returned failed"
            error = True
            package_duration = None
            logger.exception(str(e) + msg)

        return Response(make_context(error, msg, package_duration))


class PackageKnowledgeHubView(APIView):
    def get(self, request, package_id):
        """Returns the base page of knowledge hub section"""
        try:
            base_knowledge_hub = (
                PackageKnowledgeHubViewService.get_package_knowledge_hub_base_contents(
                    package_id
                )
            )
            error = False
            msg = "Knowledge hub returned successfully"

        except Exception as e:
            base_knowledge_hub = None
            error = True
            msg = "Could not return knowledge hub"
            logger.exception(str(e) + msg)

        return Response(make_context(error, msg, base_knowledge_hub))


class KnowledgeHubView(APIView):
    def get(self, request, knowledge_hub_id):
        """Returns a specific knowledge hub entry specified by the knowledge hub id"""
        try:
            knowledge_hub_content = KnowledgeHubViewService.get_knowledge_hub_contents(
                knowledge_hub_id
            )
            error = False
            msg = "Knowledge hub returned successfully"

        except Exception as e:
            knowledge_hub_content = None
            error = True
            msg = "Could not return knowledge hub"
            logger.exception(str(e) + msg)

        return Response(make_context(error, msg, knowledge_hub_content))
