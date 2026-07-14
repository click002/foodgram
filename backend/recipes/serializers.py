from api.fields import Base64ImageField
from rest_framework import serializers
from users.serializers import CustomUserSerializer

from .models import Ingredient, Recipe, RecipeIngredient, Tag


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

    def get_image(self, obj):
        request = self.context.get("request")
        if obj.image and hasattr(obj.image, "url"):
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


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

    def get_image(self, obj):
        request = self.context.get("request")
        if obj.image and hasattr(obj.image, "url"):
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.favorited_by_users.filter(user=request.user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.in_shopping_cart.filter(user=request.user).exists()
        return False


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов."""

    id = serializers.IntegerField(read_only=True)

    ingredients = serializers.ListField(
        child=serializers.DictField(),
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

    def to_internal_value(self, data):
        return super().to_internal_value(data)

    def validate(self, data):
        cooking_time = data.get("cooking_time")
        if cooking_time is not None and cooking_time < 1:
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

        for item in ingredients_data:
            if "id" not in item:
                raise serializers.ValidationError(
                    "У каждого ингредиента должно быть поле 'id'."
                )
            if "amount" not in item:
                raise serializers.ValidationError(
                    "У каждого ингредиента должно быть поле 'amount'."
                )

            ingredient_id = item["id"]
            if not Ingredient.objects.filter(id=ingredient_id).exists():
                raise serializers.ValidationError(
                    f"Ингредиент с id {ingredient_id} не существует."
                )

            try:
                amount = int(item["amount"])
                if amount <= 0:
                    raise serializers.ValidationError(
                        f"Количество ингредиента должно быть больше 0. "
                        f"Получено: {amount}"
                    )
            except (TypeError, ValueError):
                raise serializers.ValidationError(
                    f"Количество ингредиента должно быть числом. "
                    f"Получено: {item['amount']}"
                )

        ingredient_ids = [item["id"] for item in ingredients_data]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                "Ингредиенты не должны повторяться."
            )

        return ingredients_data

    def create(self, validated_data):
        user = self.context["request"].user
        if user.is_anonymous:
            raise serializers.ValidationError("Требуется авторизация")

        tags_data = validated_data.pop("tags")
        ingredients_data = validated_data.pop("ingredients")
        image = validated_data.pop("image")

        validated_data["author"] = user

        recipe = Recipe.objects.create(**validated_data)
        recipe.image = image
        recipe.save()

        recipe.tags.set(tags_data)

        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient_id=ingredient_data["id"],
                amount=ingredient_data["amount"],
            )

        return recipe

    def update(self, instance, validated_data):
        user = self.context["request"].user
        if user.is_anonymous:
            raise serializers.ValidationError(
                "Только авторизованные пользователи могут обновлять рецепты."
            )

        if "ingredients" not in self.initial_data:
            raise serializers.ValidationError(
                {"ingredients": "Это поле обязательно."}
            )

        if "tags" not in self.initial_data:
            raise serializers.ValidationError(
                {"tags": "Это поле обязательно."}
            )

        tags_data = validated_data.pop("tags", None)
        ingredients_data = validated_data.pop("ingredients", None)
        image = validated_data.pop("image", None)

        if tags_data is not None and not tags_data:
            raise serializers.ValidationError("Добавьте хотя бы один тег.")

        if ingredients_data is not None and not ingredients_data:
            raise serializers.ValidationError(
                "Добавьте хотя бы один ингредиент."
            )

        cooking_time = validated_data.get("cooking_time")
        if cooking_time is not None and cooking_time < 1:
            raise serializers.ValidationError(
                {"cooking_time": "Время приготовления должно быть больше 0."}
            )

        for field, value in validated_data.items():
            setattr(instance, field, value)

        if tags_data is not None:
            for tag_id in tags_data:
                if not Tag.objects.filter(id=tag_id).exists():
                    raise serializers.ValidationError(
                        f"Тег с id {tag_id} не существует."
                    )
            instance.tags.set(tags_data)

        if ingredients_data is not None:
            for item in ingredients_data:
                ingredient_id = item.get("id")
                if not Ingredient.objects.filter(id=ingredient_id).exists():
                    raise serializers.ValidationError(
                        f"Ингредиент с id {ingredient_id} не существует."
                    )

            instance.recipe_ingredients.all().delete()
            for ingredient_data in ingredients_data:
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient_id=ingredient_data["id"],
                    amount=ingredient_data["amount"],
                )

        if image is not None:
            if instance.image:
                instance.image.delete(save=False)
            instance.image = image

        instance.save()
        return instance
