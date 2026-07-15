from rest_framework.pagination import PageNumberPagination


class FoodgramPagination(PageNumberPagination):
    page_size_query_param = "limit"

#  "В ТЗ указан лимит "карточек" на странице."
#
#     "DEFAULT_PAGINATION_CLASS": "api.pagination.CustomPageNumberPagination",
#    "PAGE_SIZE": 6,
#  извините, что сюда пишу. вы же про это? или я неправильно понял правку...
