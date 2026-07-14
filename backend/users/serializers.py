from djoser.serializers import UserSerializer
from rest_framework import serializers

from .models import Subscription, User


class CustomUserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователя."""

    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "password",
        )
        extra_kwargs = {
            "email": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def validate(self, attrs):
        """Проверка данных перед созданием."""
        return super().validate(attrs)

    def create(self, validated_data):
        """Создает пользователя с хэшированным паролем."""
        password = validated_data.pop("password")
        user = User.objects.create_user(**validated_data, password=password)
        return user


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
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                subscriber=request.user, author=obj
            ).exists()
        return False

    def get_avatar(self, obj):
        """Возвращает полный URL аватара."""
        request = self.context.get("request")
        if obj.avatar and hasattr(obj.avatar, "url"):
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None


class UserWithRecipesSerializer(serializers.ModelSerializer):
    """Подписки пользователя и его рецепты"""

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

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
            "recipes",
            "recipes_count",
        )

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                subscriber=request.user, author=obj
            ).exists()
        return False

    def get_recipes(self, obj):
        """Возвращает рецепты автора с учетом recipes_limit."""
        request = self.context.get("request")
        recipes = obj.recipes.all().order_by("-pub_date")

        recipes_limit = request.query_params.get("recipes_limit")
        if recipes_limit:
            try:
                recipes_limit = int(recipes_limit)
                recipes = recipes[:recipes_limit]
            except ValueError:
                pass

        result = []
        for recipe in recipes:
            recipe_data = {
                "id": recipe.id,
                "name": recipe.name,
                "cooking_time": recipe.cooking_time,
                "image": recipe.image.url if recipe.image else None,
            }
            result.append(recipe_data)
        return result

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
