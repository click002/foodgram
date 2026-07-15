from django.contrib import admin

from .models import Favorite, Ingredient, Recipe, ShoppingCart, Tag

admin.site.empty_value_display = "Не задано"


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "slug",
    )

    search_fields = (
        "name",
        "slug",
    )


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "measurement_unit",
    )

    search_fields = ("name",)

    list_filter = ("measurement_unit",)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "author",
        "cooking_time",
        "pub_date",
        "favorites_count_display",
    )

    search_fields = (
        "name",
        "author__username",
    )

    list_filter = ("author", "tags", "pub_date")

    @admin.display(description="В избранном")
    def favorites_count_display(self, obj):
        """Отображение количества добавлений рецепта в избранное."""
        return obj.favorited_by_users.count()


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "recipe")

    search_fields = ("user__username", "recipe__name")

    list_filter = ("user", "recipe")


@admin.register(ShoppingCart)
class ShoppingCart(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "recipe",
        "created_at",
    )

    search_fields = (
        "user__username",
        "recipe__name",
    )

    list_filter = (
        "user",
        "recipe",
        "created_at",
    )
