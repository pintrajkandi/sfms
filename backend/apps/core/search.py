"""
Full-text search helpers (tsvector / GIN) — see CLAUDE.md §5.

Searchable models carry a SearchVectorField + GinIndex and refresh the vector on
save via `update_search_vector`. Query with SearchQuery/SearchRank, never chained
`icontains` on large tables.
"""

from __future__ import annotations

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import QuerySet


def update_search_vector(instance, fields: dict[str, str]) -> None:
    """Recompute `search_vector` from weighted fields, e.g. {"name": "A", "notes": "C"}."""
    vector = None
    for field, weight in fields.items():
        part = SearchVector(field, weight=weight, config="english")
        vector = part if vector is None else vector + part
    type(instance).objects.filter(pk=instance.pk).update(search_vector=vector)


def full_text_search(qs: QuerySet, term: str, vector_field: str = "search_vector") -> QuerySet:
    if not term:
        return qs
    query = SearchQuery(term, config="english")
    return (
        qs.filter(**{vector_field: query})
        .annotate(rank=SearchRank(vector_field, query))
        .order_by("-rank")
    )
