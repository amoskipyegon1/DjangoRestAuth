from urllib.parse import urljoin

from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from itsdangerous import URLSafeTimedSerializer

from .email import send_email
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .schemas import (
    authenticate_user_schema,
    create_user_response_schema,
    get_error_schema,
)

from .serializers import (
    TokenObtainPairWithUserSerializer,
    TokenRefreshWithUserSerializer,
    RegisterSerializer,
    ChangePasswordBodyValidationSerializer,
    SendResetPasswordEmailBodyValidationSerializer,
    ResetPasswordBodyValidationSerializer,
)

User = get_user_model()


class UserRegisterView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["User"],
        request=RegisterSerializer,
        operation_id="create_user",
        description=(
            "Creates a new user based on the provided values. Then response is"
            "attached with an authentication JWT right away. After creating an"
        ),
        responses={
            200: create_user_response_schema,
            400: get_error_schema(
                [
                    "USER_ALREADY_EXISTS",
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
        },
    )
    def post(self, request):
        data = RegisterSerializer(data=request.data)
        if data.is_valid():
            details = data.data

            user = User.objects.create(
                emailAddress=details["emailAddress"], firstName=details["firstName"]
            )
            if "lastName" in details:
                user.lastName = details["lastName"]

            user.set_password(details["password"])

            refresh = RefreshToken.for_user(user)
            user_response = {
                "user": {
                    "firstName": user.firstName,
                    "emailAddress": user.emailAddress,
                },
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
            }
            return Response(user_response, status.HTTP_201_CREATED)

        return Response(data.errors, status=status.HTTP_400_BAD_REQUEST)


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


class RefreshJSONWebToken(TokenRefreshView):
    serializer_class = TokenRefreshWithUserSerializer

    @extend_schema(
        tags=["User"],
        operation_id="token_refresh",
        description=(
            "Generate a new access_token that can be used to continue operating on Application "
            "starting from a valid refresh token."
        ),
        responses={
            200: authenticate_user_schema,
            401: {"description": "The JWT refresh token is invalid or expired."},
        },
        auth=[],
    )
    def post(self, *args, **kwargs):
        return super().post(*args, **kwargs)


class ChangePasswordView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["User"],
        request=ChangePasswordBodyValidationSerializer,
        operation_id="change_password",
        description=(
            "Changes the password of an authenticated user, but only if the old "
            "password matches."
        ),
        responses={
            204: None,
            400: get_error_schema(
                [
                    "ERROR_INVALID_OLD_PASSWORD",
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
        },
    )
    def post(self, request):
        data = ChangePasswordBodyValidationSerializer(data=request.data)

        if data.is_valid():
            post_data = data.data

            user = User.objects.get(id=request.user.id)

            if user.check_password(post_data["oldPassword"]):
                user.set_password(post_data["newPassword"])
                user.save()
                return Response("", status.HTTP_204_NO_CONTENT)

            else:
                return Response(
                    {"error": "ERROR_INVALID_OLD_PASSWORD"}, status.HTTP_400_BAD_REQUEST
                )

        return Response(data.errors, status.HTTP_400_BAD_REQUEST)


class SendResetPasswordView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["User"],
        request=SendResetPasswordEmailBodyValidationSerializer,
        operation_id="send_password_reset_email",
        description=(
            "Sends an email containing the password reset link to the email address "
            "of the user. This will only be done if a user is found with the given "
            "email address. The endpoint will not fail if the email address is not "
            "found. The link is going to the valid for {valid} hours.".format(
                valid=int(settings.RESET_PASSWORD_TOKEN_MAX_AGE)
            )
        ),
        responses={
            204: None,
            400: get_error_schema(
                ["ERROR_REQUEST_BODY_VALIDATION", "ERROR_HOSTNAME_IS_NOT_ALLOWED"]
            ),
        },
        auth=[],
    )
    def post(self, request):
        data = SendResetPasswordEmailBodyValidationSerializer(data=request.data)

        if data.is_valid():
            post_data = data.data
            try:
                user = User.objects.get(emailAddress=post_data["emailAddress"])
                base_url = post_data["base_url"]
                if not base_url.endswith("/"):
                    base_url += "/"

                signer = get_reset_password_signer()
                signed_user_id = signer.dumps(user.id)

                reset_url = urljoin(base_url, signed_user_id)

                send_email(
                    post_data["emailAddress"],
                    "Reset Password",
                    "emails/send_forgotpassword_token.html",
                    {"name": user.firstName, "link": reset_url},
                )

                return Response("", status.HTTP_200_OK)

            except User.DoesNotExist:
                return Response(
                    {"error": "USER_WITH_EMAIL_DOESN'T_EXIST"},
                    status.HTTP_400_BAD_REQUEST,
                )

        return Response(data.errors, status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):

    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["User"],
        request=ResetPasswordBodyValidationSerializer,
        operation_id="reset_password",
        description=(
            "Changes the password of a user if the reset token is valid. The "
            "**send_password_reset_email** endpoint sends an email to the user "
            "containing the token. That token can be used to change the password "
            "here without providing the old password."
        ),
        responses={
            204: None,
            400: get_error_schema(
                [
                    "BAD_TOKEN_SIGNATURE",
                    "EXPIRED_TOKEN_SIGNATURE",
                    "ERROR_USER_NOT_FOUND",
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
        },
        auth=[],
    )
    def post(self, request):
        data = ResetPasswordBodyValidationSerializer(data=request.data)
        if data.is_valid():
            post_data = data.data
            signer = get_reset_password_signer()
            user_id = signer.loads(
                post_data["token"], max_age=settings.RESET_PASSWORD_TOKEN_MAX_AGE
            )

            try:
                user = User.objects.get(id=user_id)

                user.set_password(post_data["password"])
                user.save()
                return Response("", status.HTTP_200_OK)

            except User.DoesNotExist:
                return Response(
                    {"error": "THIS_USER_DOESN'T_EXIST"},
                    status.HTTP_400_BAD_REQUEST,
                )

        return Response(data.errors, status.HTTP_400_BAD_REQUEST)


def get_reset_password_signer():
    """
    Instantiates the password reset serializer that can dump and load values.

    :return: The itsdangerous serializer.
    :rtype: URLSafeTimedSerializer
    """

    return URLSafeTimedSerializer(settings.SECRET_KEY, "user-reset-password")
