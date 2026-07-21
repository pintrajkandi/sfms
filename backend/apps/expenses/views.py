from rest_framework import viewsets

from apps.core.logging import ctx, get_logger

from .models import Expense
from .serializers import ExpenseSerializer

log = get_logger("expenses")


class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    rbac_resource = "expenses"

    def get_queryset(self):
        qs = Expense.objects.all()
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)
        return qs

    def perform_create(self, serializer):
        expense = serializer.save(
            submitted_by=self.request.user if self.request.user.is_authenticated else None
        )
        from apps.finance.ledger import _safe, post_expense

        _safe(post_expense, expense)
        log.info(
            "expense submitted amount=%s category=%s",
            expense.amount,
            expense.category,
            **ctx(
                user=getattr(self.request.user, "id", "-"),
                entity=expense.id,
                action="submit_expense",
            ),
        )
