from rest_framework import serializers

from ...models import UserAuthModel


class UserAuthSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAuthModel
        fields = (
            "email",
            "password",
        )


class UserLoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAuthModel
        fields = "email", "password"


class UserStravaLoginSerializer(serializers.ModelSerializer):
    strava_login_secret = serializers.CharField()

    class Meta:
        model = UserAuthModel
        fields = ("strava_user_id", "strava_user_token", "strava_login_secret")


class UserGarminLoginSerializer(serializers.ModelSerializer):
    garmin_login_secret = serializers.CharField()

    class Meta:
        model = UserAuthModel
        fields = ("garmin_user_id", "garmin_user_token", "garmin_login_secret")
