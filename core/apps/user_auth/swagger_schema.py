from drf_yasg import openapi
from drf_yasg.openapi import Schema
from rest_framework import status


class OtpVerificationApiSchema:
    request_schema = Schema(
        title="Request data example",
        type=openapi.TYPE_OBJECT,
        properties={
            "api_secret_key": Schema(
                type=openapi.TYPE_STRING,
                description="api secret key",
                default="Q4uxzEpua49JPOkBYE9kHA_|HQMDT_#bqBc3-U%O)T<oZ2%;%HHK*eKOtfyP9dp",
            ),
            "otp_verifier_token": Schema(
                type=openapi.TYPE_STRING,
                description="otp verifier token",
                default="b0135698-386c-4d7d-80ad-7be8ff9602b9",
            ),
            "otp": Schema(
                type=openapi.TYPE_STRING,
                description="otp code which is sent to mail",
                default="203988",
            ),
        },
    )

    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_STRING, default="false"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="Otp access token returned successfully",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "otp_access_token": Schema(
                                type=openapi.TYPE_STRING,
                                description="Otp access token",
                                default="a6d64493-4330-4dec-910e-6eb19b8dd94a",
                            ),
                        },
                    ),
                },
            ),
        ),
    }


class OtpRequestApiSchema:
    request_schema = Schema(
        title="Request data example",
        type=openapi.TYPE_OBJECT,
        properties={
            "api_secret_key": Schema(
                type=openapi.TYPE_STRING,
                description="api secret key",
                default="Q4uxzEpua49JPOkBYE9kHA_|HQMDT_#bqBc3-U%O)T<oZ2%;%HHK*eKOtfyP9dp",
            ),
            "email": Schema(
                type=openapi.TYPE_STRING,
                description="user email",
                default="user@gmai..com",
            ),
        },
    )

    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="",
            schema=Schema(
                title="Success response example",
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": Schema(type=openapi.TYPE_STRING, default="false"),
                    "message": Schema(
                        type=openapi.TYPE_STRING,
                        default="A one time password has been sent to your email. Please check your "
                        "mail and submit otp.",
                    ),
                    "data": Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "otp_verifier_token": Schema(
                                type=openapi.TYPE_STRING,
                                description="Otp verifier token",
                                default="969871e8-c789-4b4c-9780-c3ed01658de3",
                            ),
                        },
                    ),
                },
            ),
        ),
    }
