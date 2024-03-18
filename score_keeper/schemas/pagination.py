import math

from .helpers import BaseModel


class PageInfo(BaseModel):
    num_per_page: int = 10
    current_page: int = 1

    async def paginate(self, queryset):
        count = await queryset.count()

        queryset = queryset.limit(self.num_per_page).offset(
            self.num_per_page * (self.current_page - 1)
        )

        return queryset, Pagination(
            num_per_page=self.num_per_page,
            current_page=self.current_page,
            count=count,
            num_pages=math.ceil(count / self.num_per_page),
        )


class Pagination(BaseModel):
    num_per_page: int
    current_page: int
    num_pages: int

    count: int
