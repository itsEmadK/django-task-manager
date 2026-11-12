from django.core.exceptions import ObjectDoesNotExist
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from knox.models import AuthToken
from knox.views import LogoutAllView as KnoxLogoutAllView
from knox.views import LogoutView as KnoxLogoutView
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView
from rest_framework.parsers import JSONParser
from rest_framework.permissions import (
    AllowAny,
    IsAdminUser,
    IsAuthenticated,
)
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.filters import UserFilter
from accounts.models import User
from accounts.permissions import IsSelf
from accounts.serializers import (
    LoginRequestSerializer,
    LoginResponseSerializer,
    RegisterRequestSerializer,
    RegisterResponseSerializer,
    UserSerializer,
    VerifyOTPRequestSerializer,
    VerifyOTPResponseSerializer,
)
from otp.services import OTPServices


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

        user = request_serializer.save()
        challenge_id = OTPServices.request_otp(user.email)

        response_serializer = RegisterResponseSerializer(
            instance={
                "challenge_id": challenge_id,
            },
        )
        return Response(data=response_serializer.data, status=status.HTTP_201_CREATED)


class VerifyRegisterOTPView(APIView):
    @extend_schema(
        request=VerifyOTPRequestSerializer,
        responses=[VerifyOTPResponseSerializer],
    )
    def post(self, request):
        request_serializer = VerifyOTPRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        user, token_expiry, token_key = request_serializer.save()
        response_serializer = VerifyOTPResponseSerializer(
            instance={
                "user": user,
                "token": token_key,
                "token_expiry": token_expiry,
            },
        )

        return Response(response_serializer.data)


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

        email = request_serializer.validated_data["email"]
        challenge_id = OTPServices.request_otp(email=email)
        response_serializer = LoginResponseSerializer(
            instance={
                "challenge_id": challenge_id,
            }
        )
        return Response(data=response_serializer.data)


class VerifyLoginOTPView(VerifyRegisterOTPView):
    pass


class UserListView(ListAPIView):
    renderer_classes = [JSONRenderer]
    parser_classes = [JSONParser]
    permission_classes = [IsAdminUser]
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserFilter


class UserDetailView(APIView):
    renderer_classes = [JSONRenderer]
    parser_classes = [JSONParser]

    def get_permissions(self):
        if self.request.method in ["GET", "PUT", "PATCH"]:
            permission_classes = [IsAuthenticated, IsSelf]
        elif self.request.method == "DELETE":
            permission_classes = [IsAdminUser]

        return [permission() for permission in permission_classes]

    def get_object(self, request, id) -> User:
        try:
            user = User.objects.get(id=id)
            self.check_object_permissions(request=request, obj=user)
            return user
        except ObjectDoesNotExist:
            raise NotFound("user does not exist")

    @extend_schema(responses=UserSerializer)
    def get(self, request, id):
        user = self.get_object(id=id, request=request)
        serializer = UserSerializer(instance=user)  # type: ignore
        return Response(data=serializer.data)

    @extend_schema(request=UserSerializer, responses=UserSerializer)
    def patch(self, request, id):
        user = self.get_object(id=id, request=request)
        serializer = UserSerializer(
            data=request.data,  # type: ignore
            instance=user,  # type: ignore
            partial=True,  # type: ignore
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(data=UserSerializer(instance=user).data)  # type: ignore

    @extend_schema(request=UserSerializer, responses=UserSerializer)
    def put(self, request, id):
        user = self.get_object(id=id, request=request)
        serializer = UserSerializer(
            data=request.data,  # type: ignore
            instance=user,  # type: ignore
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(data=UserSerializer(instance=user).data)  # type: ignore

    def delete(self, request, id):
        user = self.get_object(id=id, request=request)
        user.delete()
        return Response(data=UserSerializer(instance=user).data)  # type: ignore


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
