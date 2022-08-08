import logging

from django.db import models

logger = logging.getLogger(__name__)


class TrainingZoneTruthTable(models.Model):
    zone_focus = models.IntegerField(blank=False, null=False)
    zone_name = models.CharField(max_length=55, null=True)
    zone_description = models.CharField(max_length=255, null=True)
    zone_basic_adaptations_description = models.CharField(max_length=255, null=True)
    zone_physiological_adaptations_description = models.CharField(
        max_length=255, null=True
    )
    power_ftp_lower_bound = models.FloatField(blank=True, null=True)
    power_ftp_upper_bound = models.FloatField(blank=True, null=True)
    heart_rate_fthr_lower_bound = models.FloatField(blank=True, null=True)
    heart_rate_fthr_upper_bound = models.FloatField(blank=True, null=True)
    max_heart_rate_lower_bound = models.FloatField(blank=True, null=True)
    max_heart_rate_upper_bound = models.FloatField(blank=True, null=True)
    rpe_lower_bound = models.IntegerField(blank=True, null=True)
    rpe_upper_bound = models.IntegerField(blank=True, null=True)
    associated_power_curve = models.DecimalField(
        decimal_places=2, max_digits=20, default=0.00
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "training_zone"
        verbose_name = "Training Zone TT"

    def __str__(self):
        zone_info = "Zone: " + str(self.zone_focus) + " " + self.zone_name
        return f"({str(self.id)}) {zone_info}"
