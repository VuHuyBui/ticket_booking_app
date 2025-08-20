from rest_framework import authentication
from rest_framework import exceptions

from django.conf import settings

import jwt
import datetime

from .models import User

def create_access_token(user_id):
    now = datetime.datetime.now()
    payload = {
        "user_id": user_id,
        "type": "access",
        "exp": now + datetime.timedelta(minutes=10),  # short lived
        "iat": now,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")

def create_refresh_token(user_id):
    now = datetime.datetime.now()
    payload = {
        "user_id": user_id,
        "type": "refresh",
        "exp": now + datetime.timedelta(days=7),  # longer lived
        "iat": now,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")

def get_tokens_for_user(user):
    if not user.is_active:
        raise exceptions.AuthenticationFailed("User is not active")


    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return {
        "access": access_token,
        "refresh": refresh_token,
    }




class JWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        # Get header
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return None  # no auth provided

        # Must be in format: Bearer <token>
        try:
            prefix, token = auth_header.split(" ")
            if prefix.lower() != "bearer":
                raise exceptions.AuthenticationFailed("Invalid token prefix")
        except ValueError:
            raise exceptions.AuthenticationFailed("Invalid Authorization header")

        # Decode JWT
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Token has expired")
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed("Invalid token")

        # Check user_id
        user_id = payload.get("user_id")
        if not user_id:
            raise exceptions.AuthenticationFailed("Token payload invalid")

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed("User not found")

        if not user.is_active:
            raise exceptions.AuthenticationFailed("User is inactive")

        # Return (user, token) tuple
        return (user, None)
