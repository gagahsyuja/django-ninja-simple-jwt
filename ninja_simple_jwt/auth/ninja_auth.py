from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from jwt import PyJWTError
from ninja.errors import AuthenticationError
from ninja.security import HttpBearer
from ninja.security.http import DecodeError

from ninja_simple_jwt.jwt.token_operations import TokenTypes, decode_token
from ninja_simple_jwt.settings import ninja_simple_jwt_settings

User = get_user_model()

class HttpJwtAuth(HttpBearer):
    def authenticate(self, request: HttpRequest, token: str) -> bool:

        try:
            access_token = decode_token(token, token_type=TokenTypes.ACCESS, verify=True)
        except PyJWTError as e:
            raise AuthenticationError(e)

        try:
            user = User.objects.get(id=access_token.get("user_id"))
        except User.DoesNotExist as e:
            raise AuthenticationError(e)

        request.user = user

        self.set_token_claims_to_user(user, access_token)

        return True

    @staticmethod
    def set_token_claims_to_user(user: AbstractBaseUser | AnonymousUser, token: dict) -> None:
        for claim, user_attribute in ninja_simple_jwt_settings.TOKEN_CLAIM_USER_ATTRIBUTE_MAP.items():
            if isinstance(user_attribute, str):
                setattr(user, user_attribute, token.get(claim))
            else:
                setattr(user, claim, token.get(claim))

    def decode_authorization(self, value: str) -> str:
        parts = value.split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise DecodeError("Invalid Authorization header")

        token = parts[1]
        return token
