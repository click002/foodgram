from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsAuthorOrReadOnly
from django.db import models
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)
from .serializers import (IngredientSerializer, RecipeCreateUpdateSerializer,
                          RecipeListSerializer, RecipeMinifiedSerializer,
                          TagSerializer)


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
    permission_classes = [IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return RecipeListSerializer
        return RecipeCreateUpdateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        """Создание рецепта с возвратом полной структуры."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        output_serializer = RecipeListSerializer(
            serializer.instance, context={"request": request}
        )

        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Обновление рецепта с возвратом полной структуры."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        output_serializer = RecipeListSerializer(
            serializer.instance, context={"request": request}
        )

        return Response(output_serializer.data)

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

        else:
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

        else:
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

        recipes = Recipe.objects.filter(in_shopping_cart__user=user)

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

        lines = ["Список покупок:\n"]
        for item in ingredients:
            name = item["ingredient__name"]
            unit = item["ingredient__measurement_unit"]
            amount = item["total_amount"]
            lines.append(f"{name} — {amount} {unit}")

        file_content = "\n".join(lines)

        response = HttpResponse(file_content, content_type="text/plain")
        response["Content-Disposition"] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_link(self, request, pk=None):
        """Возвращает короткую ссылку на рецепт."""
        recipe = self.get_object()
        short_url = request.build_absolute_uri(f"/recipes/{recipe.id}/")
        return Response({"short-link": short_url})
