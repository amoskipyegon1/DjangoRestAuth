from django.urls import path
from . import views

urlpatterns = [
    path("api/token/", views.ObtainJSONWebToken.as_view(), name="token_obtain_pair"),
]
