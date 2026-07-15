from djoser.serializers import UserSerializer
from rest_framework import serializers

from api.fields import Base64ImageField
from constants import MIN_COOKING_TIME
from users.models import (
    Ingredient, Recipe, RecipeIngredient, Subscription, Tag, User,)


class CustomUserSerializer(UserSerializer):
    """Сериализатор для профиля пользователя"""

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "avatar",
            "is_subscribed",
        )

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на данного автора."""
        request = self.context.get("request")
        return (
            request
            and request.user.is_authenticated
            and request.user.following.filter(author=obj).exists()
        )

    def get_avatar(self, obj):
        """Возвращает полный URL аватара."""
        request = self.context.get("request")
        if obj.avatar and hasattr(obj.avatar, "url"):
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None


class UserWithRecipesSerializer(CustomUserSerializer):
    """Подписки пользователя и его рецепты"""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + (
            "recipes",
            "recipes_count",
        )

    def get_recipes(self, obj):
        """Возвращает рецепты автора с учетом recipes_limit."""
        request = self.context.get("request")
        recipes = obj.recipes.all().order_by("-pub_date")

        recipes_limit = request.query_params.get("recipes_limit")
        if recipes_limit:
            try:
                recipes_limit = int(recipes_limit)
                recipes = recipes[:recipes_limit]
            except (ValueError, TypeError):
                pass

        return RecipeMinifiedSerializer(
            recipes,
            many=True,
            context=self.context,
        ).data

    def get_recipes_count(self, obj):
        """Возвращает количество рецептов автора."""
        return obj.recipes.count()


class SubscriptionSerializer(serializers.ModelSerializer):
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            "subscriber",
            "author",
            "created_at",
            "recipes_count",
        )

    def get_recipes_count(self, obj):
        return obj.author.recipes.count()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "slug")


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class RecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "name",
            "image",
            "text",
            "cooking_time",
            "tags",
            "ingredients",
            "pub_date",
        )


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Ингредиент внутри рецепта с количеством (amount)"""

    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Краткая информация о рецепте"""

    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class RecipeListSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        source="recipe_ingredients", many=True, read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        return (
            request
            and request.user.is_authenticated
            and obj.favorited_by_users.filter(user=request.user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")
        return (
            request
            and request.user.is_authenticated
            and obj.in_shopping_cart.filter(user=request.user).exists()
        )


class IngredientAmountSerializer(serializers.Serializer):
    """Сериализатор для валидации ингредиентов в рецепте"""
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов."""

    id = serializers.IntegerField(read_only=True)

    ingredients = serializers.ListField(
        child=IngredientAmountSerializer(),
        write_only=True,
    )

    tags = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
    )

    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "name",
            "text",
            "cooking_time",
            "image",
            "tags",
            "ingredients",
        )

    def validate(self, data):
        cooking_time = data.get("cooking_time")
        if cooking_time is not None and cooking_time < MIN_COOKING_TIME:
            raise serializers.ValidationError(
                {"cooking_time": "Время приготовления должно быть больше 0."}
            )

        return data

    def validate_tags(self, tags_data):
        if not tags_data:
            raise serializers.ValidationError("Добавьте хотя бы один тег.")

        if len(tags_data) != len(set(tags_data)):
            raise serializers.ValidationError("Теги не должны повторяться.")

        for tag_id in tags_data:
            if not Tag.objects.filter(id=tag_id).exists():
                raise serializers.ValidationError(
                    f"Тег с id {tag_id} не существует."
                )

        return tags_data

    def validate_ingredients(self, ingredients_data):
        if not ingredients_data:
            raise serializers.ValidationError(
                "Добавьте хотя бы один ингредиент."
            )

        ingredient_ids = [item["id"] for item in ingredients_data]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                "Ингредиенты не должны повторяться."
            )

        return ingredients_data

    def create(self, validated_data):
        user = self.context["request"].user

        tags_data = validated_data.pop("tags")
        ingredients_data = validated_data.pop("ingredients")

        validated_data["author"] = user

        recipe = Recipe.objects.create(**validated_data)

        recipe.tags.set(tags_data)

        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient["id"],
                amount=ingredient["amount"],
            )
            for ingredient in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

        return recipe

    def update(self, instance, validated_data):
        tags_data = validated_data.pop("tags", None)
        ingredients_data = validated_data.pop("ingredients", None)

        if tags_data is not None:
            instance.tags.set(tags_data)

        instance = super().update(instance, validated_data)

        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            recipe_ingredients = [
                RecipeIngredient(
                    recipe=instance,
                    ingredient_id=ingredient["id"],
                    amount=ingredient["amount"],
                )
                for ingredient in ingredients_data
            ]
            RecipeIngredient.objects.bulk_create(recipe_ingredients)

        instance.save()
        return instance
