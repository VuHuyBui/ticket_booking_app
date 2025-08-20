from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from .serializers import RegisterSerializer, LoginSerializer
from .tokens import get_tokens_for_user, create_refresh_token, create_access_token

from rest_framework_simplejwt.exceptions import AuthenticationFailed

from django.conf import settings

import jwt


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "User registered successfully"},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            tokens = get_tokens_for_user(user)

            response = Response(
                {
                    # only return the access token in body
                    "access": tokens["access"],
                    "refresh": tokens["refresh"],
                },
                status=status.HTTP_200_OK,
            )

            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RefreshTokenView(APIView):
    def post(self, request):
        refresh_token = request.data.get("refresh_token")

        if not refresh_token:
            return Response(
                {"detail": "Refresh token missing"}, status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            payload = jwt.decode(
                refresh_token, settings.JWT_SECRET_KEY, algorithms=["HS256"]
            )
            if payload.get("type") != "refresh":
                raise AuthenticationFailed("Invalid token type")
        except jwt.ExpiredSignatureError:
            return Response(
                {"detail": "Refresh token expired"}, status=status.HTTP_401_UNAUTHORIZED
            )
        except jwt.InvalidTokenError:
            return Response(
                {"detail": "Invalid refresh token"}, status=status.HTTP_401_UNAUTHORIZED
            )

        user_id = payload.get("user_id")
        if not user_id:
            return Response(
                {"detail": "Invalid payload"}, status=status.HTTP_401_UNAUTHORIZED
            )

        # Create new tokens
        access = create_access_token(user_id)
        # new_refresh = create_refresh_token(user_id)

        response = Response(
            {
                "access": access,
                "refresh": refresh_token,
            },
            status=status.HTTP_200_OK,
        )

        return response


class LogoutView(APIView):
    def post(self, request):
        response = Response(
            {"detail": "Logged out successfully"}, status=status.HTTP_200_OK
        )
        # 👇 Clear the cookie by setting it to empty & expired
        # response.delete_cookie("refresh_token")
        return response
