from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.core.logging import ctx, get_logger
from apps.core.services import ServiceError

from .models import (
    AcademicYear,
    Department,
    SchoolClass,
    SchoolSettings,
    Section,
    SupportTicket,
)
from .serializers import (
    AcademicYearSerializer,
    DepartmentSerializer,
    SchoolClassSerializer,
    SchoolSettingsSerializer,
    SectionSerializer,
    SupportTicketSerializer,
)
from .services import rollover_academic_year

log = get_logger("schools")


class DepartmentViewSet(viewsets.ModelViewSet):
    """Admin-managed departments that feed the teacher department dropdown."""

    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    rbac_resource = "departments"


class SupportTicketViewSet(viewsets.ModelViewSet):
    """School staff raise + track support requests to the platform team."""

    queryset = SupportTicket.objects.all()
    serializer_class = SupportTicketSerializer
    rbac_resource = "support"
    http_method_names = ["get", "post", "head", "options"]

    def perform_create(self, serializer):
        ticket = serializer.save()
        log.info(
            "support ticket raised category=%s subject=%s",
            ticket.category,
            ticket.subject,
            **ctx(
                user=getattr(self.request.user, "id", "-"),
                entity=ticket.id,
                action="support_ticket",
            ),
        )


class SchoolClassViewSet(viewsets.ModelViewSet):
    """Admin-managed classes that feed the student class dropdown."""

    queryset = SchoolClass.objects.prefetch_related("sections").all()
    serializer_class = SchoolClassSerializer
    rbac_resource = "classes"


class SectionViewSet(viewsets.ModelViewSet):
    serializer_class = SectionSerializer
    rbac_resource = "classes"

    def get_queryset(self):
        qs = Section.objects.select_related("school_class")
        sc = self.request.query_params.get("school_class")
        if sc:
            qs = qs.filter(school_class_id=sc)
        return qs


class SchoolSettingsViewSet(viewsets.ModelViewSet):
    """Tenant settings — there is effectively one row per school."""

    queryset = SchoolSettings.objects.all()
    serializer_class = SchoolSettingsSerializer
    rbac_resource = "settings"


class AcademicYearViewSet(viewsets.ModelViewSet):
    queryset = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer
    rbac_resource = "academic-years"

    def _sync_current(self, year):
        """Exactly one current year — setting one unsets the others."""
        if year.is_current:
            AcademicYear.objects.exclude(pk=year.pk).filter(is_current=True).update(
                is_current=False
            )

    def perform_create(self, serializer):
        self._sync_current(serializer.save())

    def perform_update(self, serializer):
        self._sync_current(serializer.save())

    @action(detail=True, methods=["post"], url_path="set-current")
    def set_current(self, request, pk=None):
        year = self.get_object()
        AcademicYear.objects.exclude(pk=year.pk).update(is_current=False)
        year.is_current = True
        year.save(update_fields=["is_current", "updated_at"])
        return Response(self.get_serializer(year).data)

    def _source(self, request):
        source_id = request.data.get("source")
        source = AcademicYear.objects.filter(pk=source_id).first()
        if source is None:
            raise ValidationError("A valid 'source' academic year is required.")
        return source

    @action(detail=True, methods=["post"], url_path="clone-fees")
    def clone_fees(self, request, pk=None):
        """Copy fee plans from ?source into this (target) year, with % uplift."""
        from apps.fees.services import clone_fee_plans

        try:
            created = clone_fee_plans(
                source_year=self._source(request),
                target_year=self.get_object(),
                increase_percent=request.data.get("increase_percent", 0),
                actor=request.user,
            )
        except ServiceError as exc:
            raise ValidationError(str(exc)) from exc
        return Response({"fee_plans_cloned": created}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def promote(self, request, pk=None):
        """Promote active students of ?source into this (target) year."""
        from apps.students.services import promote_students

        result = promote_students(
            source_year=self._source(request),
            target_year=self.get_object(),
            grade_map=request.data.get("grade_map"),
            graduating_grades=request.data.get("graduating_grades"),
            actor=request.user,
        )
        return Response(result)

    @action(detail=True, methods=["post"])
    def rollover(self, request, pk=None):
        """Full rollover into this (target) year: clone fees + promote + set current."""
        try:
            summary = rollover_academic_year(
                source_year=self._source(request),
                target_year=self.get_object(),
                grade_map=request.data.get("grade_map"),
                graduating_grades=request.data.get("graduating_grades"),
                fee_increase_percent=request.data.get("fee_increase_percent", 0),
                promote=request.data.get("promote", True),
                clone_fees=request.data.get("clone_fees", True),
                make_current=request.data.get("make_current", True),
                actor=request.user,
            )
        except ServiceError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(summary, status=status.HTTP_201_CREATED)
