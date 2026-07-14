from django.urls import include, path
from recipes.views import IngredientViewSet, RecipeViewSet, TagViewSet
from rest_framework.routers import DefaultRouter
from users.views import AvatarView, UserViewSet

router = DefaultRouter()
router.register("tags", TagViewSet, basename="tags")
router.register("ingredients", IngredientViewSet, basename="ingredients")
router.register("recipes", RecipeViewSet, basename="recipes")
router.register("users", UserViewSet, basename="users")


urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("djoser.urls.authtoken")),
    path("users/", include("djoser.urls")),
    path("users/me/avatar/", AvatarView.as_view(), name="avatar"),
    path("users/", include("djoser.urls")),
]
