from django_filters import rest_framework as filters
from recipes.models import Ingredient, Recipe


class IngredientFilter(filters.FilterSet):
    """Фильтр для ингредиентов"""

    name = filters.CharFilter(field_name="name", lookup_expr="istartswith")

    class Meta:
        model = Ingredient
        fields = ("name",)


class RecipeFilter(filters.FilterSet):
    author = filters.NumberFilter(field_name="author__id")
    tags = filters.CharFilter(method="filter_tags")
    is_favorited = filters.BooleanFilter(method="filter_is_favorited")
    is_in_shopping_cart = filters.BooleanFilter(
        method="filter_is_in_shopping_cart"
    )

    class Meta:
        model = Recipe
        fields = ("tags", "author", "is_favorited", "is_in_shopping_cart")

    def filter_tags(self, queryset, name, value):
        if not value:
            return queryset
        slugs = self.request.GET.getlist("tags")
        if not slugs:
            slugs = value.split(",")
        return queryset.filter(tags__slug__in=slugs).distinct()

    def filter_is_favorited(self, queryset, name, value):
        if value and self.request and self.request.user.is_authenticated:
            return queryset.filter(favorited_by_users__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and self.request and self.request.user.is_authenticated:
            return queryset.filter(in_shopping_cart__user=self.request.user)
        return queryset
