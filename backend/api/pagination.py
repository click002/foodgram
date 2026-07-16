from rest_framework.pagination import PageNumberPagination

from constants import PAGINATION_PAGE_SIZE


class FoodgramPagination(PageNumberPagination):
    page_size_query_param = "limit"
    page_size = PAGINATION_PAGE_SIZE
