from django.contrib.auth import get_user_model
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Subscription
from .serializers import (CustomUserCreateSerializer, CustomUserSerializer,
                          UserWithRecipesSerializer)

User = get_user_model()


class UserViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
):
    """Вьюсет для пользователей"""

    queryset = User.objects.all()

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        elif self.action in ["me", "subscriptions", "subscribe"]:
            return [permissions.IsAuthenticated()]
        elif self.action == "set_password":
            return [permissions.IsAuthenticated()]
        else:
            return [permissions.IsAuthenticatedOrReadOnly()]

    def get_serializer_class(self):
        if self.action == "create":
            return CustomUserCreateSerializer
        if self.action == "subscriptions":
            return UserWithRecipesSerializer
        return CustomUserSerializer

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def set_password(self, request):
        """Перенаправляем на Djoser для смены пароля"""
        djoser_view = DjoserUserViewSet.as_view({"post": "set_password"})
        return djoser_view(request._request)

    def perform_create(self, serializer):
        """При создании пользователя."""
        serializer.save()

    def create(self, request, *args, **kwargs):
        """Переопределяем create для отладки."""
        return super().create(request, *args, **kwargs)

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
        subscriptions = Subscription.objects.filter(
            subscriber=user
        ).select_related("author")

        authors = [sub.author for sub in subscriptions]

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
    def subscribe(self, request, pk=None):
        """Подписаться или отписаться от автора"""
        author = self.get_object()
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
                return Response(
                    {"detail": "Вы уже подписаны на этого пользователя."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            Subscription.objects.create(subscriber=user, author=author)
            serializer = UserWithRecipesSerializer(
                author, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        else:
            deleted, _ = Subscription.objects.filter(
                subscriber=user, author=author
            ).delete()
            if deleted:
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {"detail": "Вы не подписаны на этого пользователя."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class AvatarView(APIView):
    """Загрузка и удаление аватара пользователя."""

    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        """Обновляет аватар пользователя."""
        user = request.user
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

        from django.core.files.base import ContentFile

        file_name = f"avatar_{user.id}.{file_extension}"
        user.avatar.save(file_name, ContentFile(image_data), save=True)

        return Response(
            {"avatar": request.build_absolute_uri(user.avatar.url)},
            status=status.HTTP_200_OK,
        )

    def delete(self, request):
        """Удаляет аватар пользователя."""
        user = request.user

        if user.avatar:
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {"detail": "Аватар не установлен."},
            status=status.HTTP_400_BAD_REQUEST,
        )
