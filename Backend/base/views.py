from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .schemas import (
    authenticate_user_schema,
    create_user_response_schema,
    verify_user_schema,
)

from .serializers import TokenObtainPairWithUserSerializer


class ObtainJSONWebToken(TokenObtainPairView):
    """
    A slightly modified version of the ObtainJSONWebToken that uses an email as
    username.
    """

    serializer_class = TokenObtainPairWithUserSerializer

    @extend_schema(
        tags=["User"],
        operation_id="token_auth",
        description=(
            "Authenticates an existing user based on their email and their password. "
            "If successful, an access token and a refresh token will be returned."
        ),
        responses={
            200: create_user_response_schema,
            401: {
                "description": "An active user with the provided email and password "
                "could not be found."
            },
        },
        auth=[],
    )
    def post(self, *args, **kwargs):
        return super().post(*args, **kwargs)
