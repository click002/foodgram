from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import models
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import (
    IsAuthenticated, IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsAuthorOrReadOnly
from recipes.models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag
)
from users.models import Subscription

from .serializers import (
    CustomUserSerializer, IngredientSerializer, RecipeCreateUpdateSerializer,
    RecipeListSerializer, RecipeMinifiedSerializer, TagSerializer,
    UserWithRecipesSerializer
)

User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для рецептов"""

    queryset = Recipe.objects.all().order_by("-pub_date")
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return RecipeListSerializer
        return RecipeCreateUpdateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        """Добавляет или удаляет рецепт из избранного."""
        recipe = self.get_object()
        user = request.user

        if request.method == "POST":
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"detail": "Рецепт уже в избранном."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted, _ = Favorite.objects.filter(
            user=user, recipe=recipe
        ).delete()
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"detail": "Рецепта нет в избранном."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        """Добавляет или удаляет рецепт из списка покупок."""
        recipe = self.get_object()
        user = request.user

        if request.method == "POST":
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"detail": "Рецепт уже в списке покупок."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted, _ = ShoppingCart.objects.filter(
            user=user, recipe=recipe
        ).delete()
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"detail": "Рецепта нет в списке покупок."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(
        detail=False, methods=["get"], permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачивает список покупок в виде текстового файла."""
        user = request.user

        recipes = Recipe.objects.filter(shopping_cart_items__user=user)

        if not recipes.exists():
            response = HttpResponse(
                "Список покупок пуст.", content_type="text/plain"
            )
            response["Content-Disposition"] = (
                'attachment; filename="shopping_list.txt"'
            )
            return response

        ingredients = (
            RecipeIngredient.objects.filter(recipe__in=recipes)
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total_amount=models.Sum("amount"))
            .order_by("ingredient__name")
        )

        file_content = self._prepare_shopping_text(ingredients)

        response = HttpResponse(file_content, content_type="text/plain")
        response["Content-Disposition"] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    def _prepare_shopping_text(self, ingredients):
        """Подготавливает текст для списка покупок."""
        lines = ["Список покупок:"]
        for item in ingredients:
            name = item["ingredient__name"]
            unit = item["ingredient__measurement_unit"]
            amount = item["total_amount"]
            lines.append(f"{name} — {amount} {unit}")
        return "\n".join(lines)

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_link(self, request, pk=None):
        """Возвращает короткую ссылку на рецепт."""
        recipe = self.get_object()
        short_url = request.build_absolute_uri(f"/recipes/{recipe.id}/")
        return Response({"short-link": short_url})


class UserViewSet(DjoserUserViewSet):
    """Вьюсет для пользователей"""

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def me(self, request):
        """Возвращает профиль текущего пользователя"""
        serializer = CustomUserSerializer(
            request.user, context={"request": request}
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def subscriptions(self, request):
        """
        Возвращает список авторов, на которых подписан текущий пользователь
        """
        user = request.user

        authors = User.objects.filter(
            followers__subscriber=user
        ).distinct()

        page = self.paginate_queryset(authors)
        if page is not None:
            serializer = UserWithRecipesSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = UserWithRecipesSerializer(
            authors, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        """Подписаться или отписаться от автора"""
        author = get_object_or_404(User, pk=id)
        user = request.user

        if request.method == "POST":
            if user == author:

                return Response(
                    {"detail": "Нельзя подписаться на самого себя."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if Subscription.objects.filter(
                subscriber=user, author=author
            ).exists():
                print("🔍 5. subscription already exists")
                return Response(
                    {"detail": "Вы уже подписаны на этого пользователя."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            Subscription.objects.create(subscriber=user, author=author)
            serializer = UserWithRecipesSerializer(
                author, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted, _ = Subscription.objects.filter(
            subscriber=user, author=author
        ).delete()
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"detail": "Вы не подписаны на этого пользователя."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(
        detail=False,
        methods=["put", "delete"],
        permission_classes=[permissions.IsAuthenticated],
        url_path="me/avatar",
    )
    def avatar(self, request):
        """Загрузка и удаление аватара пользователя."""
        user = request.user

        if request.method == "PUT":
            avatar_base64 = request.data.get("avatar")
            if not avatar_base64:
                return Response(
                    {"detail": 'Поле "avatar" обязательно.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            file_extension = "png"
            if "data:image/" in avatar_base64:
                try:
                    mime_part = avatar_base64.split(";")[0]
                    file_extension = mime_part.split("/")[-1]
                except IndexError:
                    pass

            if "," in avatar_base64:
                avatar_base64 = avatar_base64.split(",")[1]

            try:
                import base64

                image_data = base64.b64decode(avatar_base64)
            except Exception:
                return Response(
                    {"detail": "Неверный формат Base64."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if user.avatar:
                user.avatar.delete(save=False)

            file_name = f"avatar_{user.id}.{file_extension}"
            user.avatar.save(file_name, ContentFile(image_data), save=True)

            return Response(
                {"avatar": request.build_absolute_uri(user.avatar.url)},
                status=status.HTTP_200_OK,
            )

        if user.avatar:
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"detail": "Аватар не установлен."},
            status=status.HTTP_400_BAD_REQUEST,
        )
