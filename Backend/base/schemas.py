from django.conf import settings

from drf_spectacular.plumbing import build_object_type
from rest_framework_simplejwt.settings import api_settings as jwt_settings


user_response_schema = {
    "user": {
        "type": "object",
        "description": "An object containing information related to the user.",
        "properties": {
            "firstName": {
                "type": "string",
                "description": "The first name of related user.",
            },
            "emailAddress": {
                "type": "string",
                "format": "email",
                "description": "The username of the related user. This is always "
                "an email address.",
            },
        },
    },
}

access_token_schema = {
    "access_token": {
        "type": "string",
        "description": "'access_token' can be used to authorize for other endpoints that require authorization. "
        "This token will be valid for {valid} minutes.".format(
            valid=int(
                settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds() / 60
            ),
        ),
    },
}

refresh_token_schema = {
    "refresh_token": {
        "type": "string",
        "description": "'refresh_token' can be used to get a new valid 'access_token'. "
        "This token will be valid for {valid} hours.".format(
            valid=int(
                settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds() / 3600
            ),
        ),
    }
}

create_user_response_schema = build_object_type(
    {
        **user_response_schema,
        **access_token_schema,
        **refresh_token_schema,
    }
)

if jwt_settings.ROTATE_REFRESH_TOKENS:
    authenticate_user_schema = create_user_response_schema
else:
    authenticate_user_schema = build_object_type(
        {
            **user_response_schema,
            **access_token_schema,
        }
    )

verify_user_schema = build_object_type(user_response_schema)
