from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import (
    LoginRequestSerializer,
    LoginResponseSerializer,
    RegisterRequestSerializer,
    RegisterResponseSerializer,
)


class RegisterUser(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=RegisterRequestSerializer,
        responses=RegisterResponseSerializer,
    )
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        request_serializer = RegisterRequestSerializer(
            data={
                "email": email,
                "password": password,
            },
        )
        request_serializer.is_valid(raise_exception=True)

        user, token = request_serializer.save()
        response_serializer = RegisterResponseSerializer(
            instance={"user": user, "token": token.key},
        )
        return Response(data=response_serializer.data, status=status.HTTP_201_CREATED)


class Login(APIView):
    @extend_schema(
        request=LoginRequestSerializer,
        responses=LoginResponseSerializer,
    )
    def post(self, request):
        request_serializer = LoginRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        user = request_serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)

        response_serializer = LoginResponseSerializer(
            instance={
                "user": user,
                "token": token.key,
            }
        )
        return Response(data=response_serializer.data)
