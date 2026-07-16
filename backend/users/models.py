from django.contrib.auth.models import AbstractUser
from django.db import models

from constants import (
    MAX_LENGTH_EMAIL, MAX_LENGTH_FIRST_NAME, MAX_LENGTH_LAST_NAME
)


class User(AbstractUser):
    """
    Кастомная модель Пользователя с аватаром. Вход только по email.
    """

    first_name = models.CharField(
        max_length=MAX_LENGTH_FIRST_NAME,
        verbose_name="Имя",
    )
    last_name = models.CharField(
        max_length=MAX_LENGTH_LAST_NAME,
        verbose_name="Фамилия",
    )

    email = models.EmailField(
        max_length=MAX_LENGTH_EMAIL,
        unique=True,
        verbose_name="Email",
    )
    avatar = models.ImageField(
        upload_to="users/avatars/",
        null=True,
        blank=True,
        verbose_name="Аватар",
    )

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["username"]

    def __str__(self):
        return f"{self.username} ({self.first_name} {self.last_name})"


class Subscription(models.Model):
    """ "Модель подписки на автора рецептов"""

    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="followers",
        verbose_name="Автор",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата подписки",
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["subscriber", "author"],
                name="unique_subscriber_author"
            )
        ]

    def __str__(self):
        return (
            f"{self.subscriber.username} "
            f"подписан на {self.author.username}"
        )
