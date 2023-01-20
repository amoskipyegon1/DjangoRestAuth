from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.validators import UniqueValidator
from drf_spectacular.utils import extend_schema_serializer


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("emailAddress", "firstName", "is_staff", "id")


class PublicUserSerializer(serializers.ModelSerializer):
    """
    Serializer that exposes only fields that can be shared
    about the user for the whole group.
    """

    class Meta:
        model = User
        fields = ("id", "emailAddress", "firstName")
        extra_kwargs = {
            "id": {"read_only": True},
        }


class ResetPasswordBodyValidationSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(min_length=6)


class SendResetPasswordEmailBodyValidationSerializer(serializers.Serializer):
    emailAddress = serializers.EmailField(
        help_text="The email address of the user that has requested a password reset."
    )
    base_url = serializers.URLField(
        help_text="The base URL where the user can reset his password. The reset "
        "token is going to be appended to the base_url (base_url "
        "'/token')."
    )


class ChangePasswordBodyValidationSerializer(serializers.Serializer):
    oldPassword = serializers.CharField(min_length=6)
    newPassword = serializers.CharField(min_length=6)


class RegisterSerializer(serializers.Serializer):
    emailAddress = serializers.EmailField(
        help_text="The email address is also going to be the username.",
        validators=[UniqueValidator(queryset=User.objects.all())],
    )
    firstName = serializers.CharField(min_length=2, max_length=150)
    lastName = serializers.CharField(min_length=2, max_length=150, required=False)
    password = serializers.CharField(min_length=6)


class TokenObtainPairWithUserSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        return super().get_token(user)

    def validate(self, attrs):
        data = super().validate(attrs)
        user = {
            "user": {
                "firstName": self.user.firstName,
                "emailAddress": self.user.emailAddress,
            },
            "access_token": data["access"],
            "refresh_token": data["refresh"],
        }
        return user


@extend_schema_serializer(exclude_fields=["refresh"], deprecate_fields=["token"])
class TokenRefreshWithUserSerializer(TokenRefreshSerializer):
    refresh_token = serializers.CharField(required=False)
    token = serializers.CharField(
        required=False, help_text="Deprecated. Use `refresh_token` instead."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        del self.fields["refresh"]

    def validate(self, attrs):
        print("---------------------------------")
        attrs["refresh"] = attrs.pop("refresh_token", attrs.get("token"))
        data = super().validate(attrs)
        tokens = {
            "refresh_token": attrs.get("refresh"),
            "access_token": data["access"],
        }
        return tokens
