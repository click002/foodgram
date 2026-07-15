from djoser.serializers import UserSerializer
from rest_framework import serializers

from backend.recipes.serializers2 import RecipeMinifiedSerializer
from .models import Subscription, User


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
