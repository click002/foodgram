from constants import (MAX_LENGTH_INGREDIENT_NAME, MAX_LENGTH_RECIPE_NAME,
                       MAX_LENGTH_TAG_NAME, MAX_LENGTH_TAG_SLUG,
                       MAX_LENGTH_UNIT)
from django.db import models


class Tag(models.Model):
    """Фильтрация рецептов по тегам"""

    name = models.CharField(
        max_length=MAX_LENGTH_TAG_NAME,
        unique=True,
        verbose_name="Название Тега",
    )

    slug = models.SlugField(
        max_length=MAX_LENGTH_TAG_SLUG, unique=True, verbose_name="Слаг"
    )

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиента"""

    name = models.CharField(
        max_length=MAX_LENGTH_INGREDIENT_NAME,
        verbose_name="Название ингредиента",
    )

    measurement_unit = models.CharField(
        max_length=MAX_LENGTH_UNIT, verbose_name="Единица измерения"
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ["name"]
        unique_together = ("name", "measurement_unit")

    def __str__(self):
        return f"{self.name} {self.measurement_unit}"


class Recipe(models.Model):
    """Модель рецепта"""

    author = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор рецепта",
    )
    name = models.CharField(
        max_length=MAX_LENGTH_RECIPE_NAME, verbose_name="Название рецепта"
    )

    image = models.ImageField(
        upload_to="recipe/images/", verbose_name="Изображение рецепта"
    )

    text = models.TextField(verbose_name="Описание рецепта")

    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время приготовление (мин)",
    )

    tags = models.ManyToManyField(
        Tag,
        related_name="recipes",
        verbose_name="Теги",
    )

    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        related_name="recipes",
        verbose_name="Ингредиенты",
    )

    pub_date = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата публикации"
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ["-pub_date"]
        unique_together = ("author", "name")

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Промежуточная модель для связи Рецепта и Ингредиента"""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
        verbose_name="Рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
        verbose_name="Ингредиент",
    )

    amount = models.PositiveSmallIntegerField(verbose_name="Количество")

    class Meta:
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецептах"
        unique_together = ("recipe", "ingredient")

    def __str__(self):
        return f"{self.ingredient.name} в {self.recipe.name}"


class Favorite(models.Model):
    """Избранное"""

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorited_by_users",
        verbose_name="Рецепт",
    )

    class Meta:
        verbose_name = "Избранный рецепт"
        verbose_name_plural = "Избранные рецепты"
        unique_together = ("user", "recipe")
        ordering = ["recipe__name"]

    def __str__(self):
        return f"Автор {self.user.username}, рецепт {self.recipe.name}"


class ShoppingCart(models.Model):
    """Модель корзины покупок"""

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="shopping_cart",
        verbose_name="Корзина пользователя",
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="in_shopping_cart",
        verbose_name="Рецепт в корзине",
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата добавления"
    )

    class Meta:
        verbose_name = "Корзина покупок"
        verbose_name_plural = "Корзины покупок"
        unique_together = ("user", "recipe")

    def __str__(self):
        return f"Покупатель {self.user} добавил {self.recipe} в корзину"
