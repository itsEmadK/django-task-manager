from drf_spectacular.utils import extend_schema
from knox.models import AuthToken
from knox.views import LogoutAllView as KnoxLogoutAllView
from knox.views import LogoutView as KnoxLogoutView
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import (
    LoginRequestSerializer,
    LoginResponseSerializer,
    RegisterRequestSerializer,
    RegisterResponseSerializer,
    UserSerializer,
)


class RegisterUserView(APIView):
    permission_classes = [AllowAny]
    renderer_classes = [JSONRenderer]
    parser_classes = [JSONParser]

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

        user, token, token_key = request_serializer.save()
        response_serializer = RegisterResponseSerializer(
            instance={
                "user": user,
                "token": token_key,
                "expiry": token.expiry,
            },
        )
        return Response(data=response_serializer.data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]
    renderer_classes = [JSONRenderer]
    parser_classes = [JSONParser]

    @extend_schema(
        request=LoginRequestSerializer,
        responses=LoginResponseSerializer,
    )
    def post(self, request):
        request_serializer = LoginRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        user = request_serializer.validated_data["user"]
        token, token_key = AuthToken.objects.create(user=user)  # type: ignore

        response_serializer = LoginResponseSerializer(
            instance={
                "user": user,
                "token": token_key,
                "expiry": token.expiry,
            }
        )
        return Response(data=response_serializer.data)


class CurrentUserView(APIView):
    renderer_classes = [JSONRenderer]
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=UserSerializer)
    def get(self, request: Request):
        serializer = UserSerializer(instance=request.user)  # type: ignore
        return Response(data=serializer.data)


class LogoutView(KnoxLogoutView):
    def get_post_response(self, request):
        return Response("successfully logged out", status=status.HTTP_200_OK)


class LogoutAllView(KnoxLogoutAllView):
    def get_post_response(self, request):
        return Response("successfully revoked all sessions", status=status.HTTP_200_OK)
