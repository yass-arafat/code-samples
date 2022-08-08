from ckeditor.fields import RichTextField
from django.db import models


class InformationSection(models.Model):
    title = models.CharField("Section Title", max_length=255)
    sequence = models.IntegerField("Sequence")
    is_active = models.BooleanField("Active", default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "information_section"
        verbose_name = "Information Section"
        ordering = ["sequence"]

    def __str__(self):
        return self.title


class InformationDetail(models.Model):
    section = models.ForeignKey(
        "InformationSection", related_name="detail_pages", on_delete=models.CASCADE
    )
    title = models.CharField("Page Title", max_length=255)
    body = RichTextField("Page Body")
    sequence = models.IntegerField("Sequence")
    is_active = models.BooleanField("Active", default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "information_detail"
        verbose_name = "Information Detail"
        ordering = ["sequence"]

    def __str__(self):
        return f"({str(self.id)}) {self.section.title} - {self.title}"
