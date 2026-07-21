from rest_framework import viewsets

from apps.core.search import full_text_search, update_search_vector

from .models import InventoryItem
from .serializers import InventoryItemSerializer

_SEARCH_FIELDS = {"name": "A", "sku": "A", "brand": "B", "supplier_name": "C"}


class InventoryItemViewSet(viewsets.ModelViewSet):
    serializer_class = InventoryItemSerializer
    rbac_resource = "inventory"

    def get_queryset(self):
        qs = InventoryItem.objects.alive()
        term = self.request.query_params.get("search")
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)
        if term:
            qs = full_text_search(qs, term)
        return qs

    def perform_create(self, serializer):
        item = serializer.save()
        update_search_vector(item, _SEARCH_FIELDS)

    def perform_update(self, serializer):
        item = serializer.save()
        update_search_vector(item, _SEARCH_FIELDS)

    def perform_destroy(self, instance):
        instance.soft_delete()
