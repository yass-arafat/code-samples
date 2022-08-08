from django.contrib import admin

from . import models

admin.site.register(
    [
        models.UserProfile,
        models.UserPersonaliseData,
        models.UserScheduleData,
        models.ProfileImage,
        models.UserTrainingAvailability,
        models.CommuteWeek,
        models.AvailableTrainingDurationsInHour,
    ]
)
