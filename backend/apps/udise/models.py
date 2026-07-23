"""
UDISE school register — a platform-level list of external schools (used for
outreach). Lives in the PUBLIC schema (SHARED_APPS) and is managed from the
public Django admin; it is not tenant business data.

Only the columns needed for outreach are kept from the UDISE export, plus a
`mail_sent` flag.
"""

from django.db import models


class UdiseSchool(models.Model):
    state_id = models.CharField(max_length=20, blank=True)
    state_name = models.CharField(max_length=200, blank=True)
    district_name = models.CharField(max_length=200, blank=True)
    address = models.TextField(blank=True)
    class_to = models.CharField(max_length=10, blank=True)  # highest class, e.g. "5"
    email = models.EmailField(max_length=254, blank=True)
    school_name = models.CharField(max_length=300)
    mail_sent = models.BooleanField(default=False)  # outreach: yes/no

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "UDISE school"
        verbose_name_plural = "UDISE schools"
        ordering = ("school_name",)
        constraints = [
            # Idempotent imports: the same school row is never duplicated.
            models.UniqueConstraint(
                fields=["school_name", "address", "state_id"],
                name="uniq_udise_school",
            )
        ]

    def __str__(self) -> str:
        return self.school_name
