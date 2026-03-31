"""
Custom NinjaJWT input schema for email-based authentication.
Matches allauth's ACCOUNT_LOGIN_METHODS = {'email'} configuration.
"""
from typing import Dict, Optional, Type, cast

from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.http import HttpRequest
from ninja import Schema
from ninja_jwt import exceptions
from ninja_jwt.schema import TokenInputSchemaMixin
from ninja_jwt.settings import api_settings
from ninja_jwt.tokens import RefreshToken
from pydantic import SecretStr, ValidationInfo, model_validator


class EmailTokenObtainPairOutputSchema(Schema):
    """Response schema returning email (not username) alongside the JWT pair."""
    email: str
    access: str
    refresh: str


class EmailTokenObtainPairInputSchema(Schema, TokenInputSchemaMixin):
    """
    Accepts { email, password } and authenticates via allauth's
    AuthenticationBackend (which resolves the user by email).
    """

    email: str
    password: SecretStr

    @model_validator(mode="before")
    @classmethod
    def validate_inputs(cls, values):
        # values may be a DjangoGetter proxy; normalise to a plain dict
        raw: dict = values._obj if hasattr(values, "_obj") else dict(values)
        if not raw.get("email"):
            raise exceptions.ValidationError({"email": "email is required"})
        if not raw.get("password"):
            raise exceptions.ValidationError({"password": "password is required"})
        return values

    @model_validator(mode="after")
    def post_validate(self, info: ValidationInfo) -> "EmailTokenObtainPairInputSchema":
        request: Optional[HttpRequest] = (
            info.context.get("request") if info.context else None
        )
        password = (
            self.password.get_secret_value()
            if isinstance(self.password, SecretStr)
            else self.password
        )

        # allauth's AuthenticationBackend supports the `email` kwarg
        self._user = authenticate(request, email=self.email, password=password)

        if not (self._user is not None and self._user.is_active):
            raise exceptions.AuthenticationFailed(
                self._default_error_messages["no_active_account"]
            )

        self.check_user_authentication_rule()

        token_data = self.__class__.get_token(self._user)
        self.__dict__.update(token_data=token_data)

        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, self._user)

        return self

    @classmethod
    def get_response_schema(cls) -> Type[Schema]:
        return EmailTokenObtainPairOutputSchema

    @classmethod
    def get_token(cls, user) -> Dict:
        refresh = cast(RefreshToken, RefreshToken.for_user(user))
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

    def get_response_schema_init_kwargs(self) -> dict:
        return {
            "email": self.email,
            **self.__dict__.get("token_data", {}),
        }

    def to_response_schema(self):
        return self.get_response_schema()(**self.get_response_schema_init_kwargs())
