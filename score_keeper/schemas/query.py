from typing import Any

from .pagination import PageInfo


class Query:
    filters: Any
    sorts: Any
    resolves: Any
    page_info: PageInfo

    async def apply(self, queryset):
        if self.filters:
            queryset = queryset.filter(**{x.field: x.value for x in self.filters})

        if self.sorts:
            queryset = queryset.order_by(*self.sorts)

        if self.resolves:
            queryset = queryset.prefetch_related(*self.resolves)

        return await self.page_info.paginate(queryset)
