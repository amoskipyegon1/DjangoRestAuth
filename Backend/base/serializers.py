from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model

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
    old_password = serializers.CharField(min_length=6)
    new_password = serializers.CharField(min_length=6)


class RegisterSerializer(serializers.Serializer):
    firstName = serializers.CharField(min_length=2, max_length=150)
    emailAddress = serializers.EmailField(
        help_text="The email address is also going to be the username."
    )
    password = serializers.CharField(min_length=6)


class TokenObtainPairWithUserSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        return super().get_token(user)

    def validate(self, attrs):
        print("------------------------------------------------")
        data = super().validate(attrs)
        print(self.user)
        user = {
            "user": {
                "firstName": self.user.firstName,
                "emailAddress": self.user.emailAddress,
            },
            "access_token": data["access"],
            "refresh_token": data["refresh"],
        }
        return user
