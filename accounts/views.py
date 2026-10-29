from django.core.exceptions import ObjectDoesNotExist
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import NotFound
from rest_framework.parsers import JSONParser
from rest_framework.permissions import (
    AllowAny,
    IsAdminUser,
    IsAuthenticated,
)
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.permissions import IsSelf
from accounts.serializers import (
    LoginRequestSerializer,
    LoginResponseSerializer,
    RegisterRequestSerializer,
    RegisterResponseSerializer,
    UserSerializer,
)


class RegisterUser(APIView):
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

        user, token = request_serializer.save()
        response_serializer = RegisterResponseSerializer(
            instance={"user": user, "token": token.key},
        )
        return Response(data=response_serializer.data, status=status.HTTP_201_CREATED)


class Login(APIView):
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
        token, _ = Token.objects.get_or_create(user=user)

        response_serializer = LoginResponseSerializer(
            instance={
                "user": user,
                "token": token.key,
            }
        )
        return Response(data=response_serializer.data)


class UserList(APIView):
    renderer_classes = [JSONRenderer]
    parser_classes = [JSONParser]
    permission_classes = [IsAdminUser]

    @extend_schema(responses=UserSerializer)
    def get(self, _):
        users = User.objects.all()
        serializer = UserSerializer(instance=users, many=True)  # type: ignore
        return Response(data=serializer.data)


class UserDetail(APIView):
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
