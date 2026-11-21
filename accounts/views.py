from drf_spectacular.utils import extend_schema
from knox.models import AuthToken
from knox.views import LogoutAllView as KnoxLogoutAllView
from knox.views import LogoutView as KnoxLogoutView
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveAPIView,
)
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Profile
from accounts.serializers import (
    LoginRequestSerializer,
    LoginResponseSerializer,
    ReadProfileSerializer,
    WriteProfileSerializer,
    RegisterRequestSerializer,
    RegisterResponseSerializer,
    UserSerializer,
)
from .errors import ProfileAlreadyExists


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


class CurrentUserView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class CurrentUserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def get_serializer_context(self):
        context = {"request": self.request}
        return context

    def get_profile(self):
        try:
            return Profile.objects.get(user=self.request.user)
        except Profile.DoesNotExist:
            raise NotFound("You have not created a profile yet")

    @extend_schema(responses=[ReadProfileSerializer])
    def get(self, request):
        profile = self.get_profile()
        serializer = ReadProfileSerializer(instance=profile, context=self.get_serializer_context())  # type: ignore
        return Response(data=serializer.data)

    @extend_schema(request=WriteProfileSerializer, responses=[ReadProfileSerializer])
    def post(self, request):
        profile_already_exists = Profile.objects.filter(user=self.request.user).exists()
        if profile_already_exists:
            raise ProfileAlreadyExists()

        serializer = WriteProfileSerializer(
            data=request.data,  # type: ignore
            context={"user": self.request.user},  # type: ignore
        )
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()

        return Response(
            data=ReadProfileSerializer(instance=profile, context=self.get_serializer_context()).data,  # type: ignore
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(request=WriteProfileSerializer, responses=[ReadProfileSerializer])
    def patch(self, request):
        instance = self.get_profile()
        serializer = WriteProfileSerializer(
            instance=instance,  # type: ignore
            data=request.data,  # type: ignore
            context={"user": self.request.user},  # type: ignore
            partial=True,  # type: ignore
        )
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()

        return Response(
            data=ReadProfileSerializer(instance=profile, context=self.get_serializer_context()).data,  # type: ignore
        )

    @extend_schema(request=WriteProfileSerializer, responses=[ReadProfileSerializer])
    def put(self, request):
        instance = self.get_profile()
        serializer = WriteProfileSerializer(
            instance=instance,  # type: ignore
            data=request.data,  # type: ignore
            context={"user": self.request.user},  # type: ignore
        )
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()

        return Response(
            data=ReadProfileSerializer(instance=profile, context=self.get_serializer_context()).data,  # type: ignore
        )


class LogoutView(KnoxLogoutView):
    def get_post_response(self, request):
        return Response("successfully logged out", status=status.HTTP_200_OK)


class LogoutAllView(KnoxLogoutAllView):
    def get_post_response(self, request):
        return Response("successfully revoked all sessions", status=status.HTTP_200_OK)
