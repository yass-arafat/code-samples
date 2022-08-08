from django.db import models


class CommonModelManager(models.Manager):
    def filter_active(self, **extra_fields):
        return self.filter(is_active=True, **extra_fields)
