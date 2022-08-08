from django.db import models


class SessionScoreCategoriesTruthTable(models.Model):
    score_category = models.CharField(max_length=55, null=True, blank=False)
    score_range_lower_bound = models.IntegerField(null=True, blank=False)
    score_range_upper_bound = models.IntegerField(null=True, blank=False)

    class Meta:
        db_table = "session_score_categories_truth_table"
        verbose_name = "Session Score Categories Truth Table"

    def __str__(self):
        return f"({str(self.id)}) {self.score_category}"
