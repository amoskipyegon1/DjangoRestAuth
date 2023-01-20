from django.urls import path
from . import views

urlpatterns = [
    path("api/token/", views.ObtainJSONWebToken.as_view(), name="token_obtain_pair"),
    path(
        "api/token/refresh/", views.RefreshJSONWebToken.as_view(), name="token_refresh"
    ),
    path("api/register", views.UserRegisterView.as_view(), name="register_user"),
    path(
        "api/change-password",
        views.ChangePasswordView.as_view(),
        name="change_user_password",
    ),
]
