from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Subscription, User

admin.site.empty_value_display = "Не задано"


@admin.register(User)
class FoodgramUserAdmin(UserAdmin):
    list_display = (
        "id",
        "username",
        "email",
        "first_name",
        "last_name",
    )

    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
    )

    list_filter = ("is_active", "is_staff", "is_superuser", "date_joined")

    fieldsets = UserAdmin.fieldsets + (
        ("Дополнительные поля", {"fields": ("avatar")}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Дополнительные поля", {"fields": ("avatar")}),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "subscriber", "author", "created_at")

    search_fields = ("subscriber__username",)
