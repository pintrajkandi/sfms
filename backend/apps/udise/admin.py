import io

from django import forms
from django.contrib import messages
from django.contrib.admin import action as admin_action
from django.shortcuts import redirect, render
from unfold.admin import ModelAdmin
from unfold.decorators import action as unfold_action

from apps.tenants.admin_site import platform_admin

from .importer import import_rows
from .models import UdiseSchool


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single = super().clean
        if isinstance(data, (list, tuple)):
            return [single(d, initial) for d in data]
        return [single(data, initial)]


class CsvImportForm(forms.Form):
    csv_files = MultipleFileField(
        label="UDISE CSV file(s)",
        help_text="Select one or many raw UDISE export .csv files.",
    )


class UdiseSchoolChangeListForm(forms.ModelForm):
    """Edit `mail_sent` as a True/False dropdown instead of a checkbox."""

    mail_sent = forms.TypedChoiceField(
        label="Mail sent",
        choices=[("True", "True"), ("False", "False")],
        coerce=lambda v: v in ("True", "true", "1", True),
        widget=forms.Select(),
    )

    class Meta:
        model = UdiseSchool
        fields = ["mail_sent"]  # only field editable from the changelist


class UdiseSchoolAdmin(ModelAdmin):
    list_display = (
        "school_name",
        "district_name",
        "state_name",
        "class_to",
        "email",
        "mail_sent",
    )
    # Keep only cheap filters. state_name/district_name/class_to as list_filter
    # forced a `SELECT DISTINCT` over ~1M rows on every page load (~150-180ms
    # each); use search for those instead.
    list_filter = ("mail_sent",)
    search_fields = ("school_name", "email", "address", "district_name", "state_name")
    search_help_text = "Search by school name, email, address, district or state."
    list_editable = ("mail_sent",)  # True/False dropdown, straight from the list
    list_per_page = 50
    # Skip the second, full COUNT(*) Django runs for the "N results" line.
    show_full_result_count = False
    # No date_hierarchy: the created_at month drill-down ran a distinct-by-month
    # aggregation over ~1M rows every load (~400ms) for little value here.

    # Unfold renders these as buttons at the top of the changelist.
    actions_list = ("import_csv",)
    # Bulk (checkbox) actions.
    actions = ("mark_mail_sent", "mark_mail_not_sent")

    def get_changelist_form(self, request, **kwargs):
        kwargs.setdefault("form", UdiseSchoolChangeListForm)
        return super().get_changelist_form(request, **kwargs)

    @admin_action(description="Mark selected as mail sent")
    def mark_mail_sent(self, request, queryset):
        n = queryset.update(mail_sent=True)
        self.message_user(request, f"{n} school(s) marked as mail sent.", messages.SUCCESS)

    @admin_action(description="Mark selected as NOT mail sent")
    def mark_mail_not_sent(self, request, queryset):
        n = queryset.update(mail_sent=False)
        self.message_user(request, f"{n} school(s) marked as not sent.", messages.SUCCESS)

    # ---- CSV upload / import (Unfold changelist action button) -------------
    @unfold_action(description="Import CSV", url_path="import-csv")
    def import_csv(self, request):
        if request.method == "POST":
            form = CsvImportForm(request.POST, request.FILES)
            if form.is_valid():
                uploads = request.FILES.getlist("csv_files")
                total_new = total_rows = 0
                for upload in uploads:
                    stream = io.TextIOWrapper(upload.file, encoding="utf-8", errors="replace")
                    result = import_rows(stream)
                    total_new += result["created"]
                    total_rows += result["rows"]
                self.message_user(
                    request,
                    f"Imported {total_new} new school(s) from {len(uploads)} file(s) "
                    f"({total_rows} rows scanned).",
                    messages.SUCCESS,
                )
                return redirect("platform_admin:udise_udiseschool_changelist")
        else:
            form = CsvImportForm()
        context = {
            **self.admin_site.each_context(request),
            "title": "Import UDISE schools (CSV)",
            "form": form,
            "opts": self.model._meta,
        }
        return render(request, "admin/udise/import_csv.html", context)


platform_admin.register(UdiseSchool, UdiseSchoolAdmin)
