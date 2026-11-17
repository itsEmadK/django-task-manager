from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from knox.models import AuthToken
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.exceptions import ValidationError as DrfValidationError
from rest_framework.fields import CharField, DateTimeField, EmailField, IntegerField
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework.validators import UniqueValidator

from accounts.models import Profile, User


def drf_validate_password(value):
    try:
        validate_password(value)
    except DjangoValidationError as e:
        raise DrfValidationError(e.messages)


class UserSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = [
            "id",
            "email",
        ]

    def save(self):
        raise NotImplementedError("this is a read-only serializer")


class ProfileSerializer(ModelSerializer):
    """Requires 'user' to be included in the serializer
    context if used for profile creation"""

    user = UserSerializer(
        read_only=True,  # type: ignore
    )

    class Meta:
        model = Profile
        fields = [
            "name",
            "age",
            "user",
        ]

    def save(self):
        if self.instance:
            return super().save()
        else:
            user = self.context["user"]
            return super().save(user=user)


class RegisterRequestSerializer(Serializer):
    email = EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())],
    )
    password = CharField(write_only=True, validators=[drf_validate_password])

    def save(self):
        user: User = User.objects.create_user(**self.validated_data)
        token, token_key = AuthToken.objects.create(user=user)  # type: ignore

        return (user, token, token_key)


class RegisterResponseSerializer(Serializer):
    user = UserSerializer(read_only=True)  # type: ignore
    token = CharField(read_only=True)
    expiry = DateTimeField(read_only=True)


class LoginRequestSerializer(Serializer):
    email = EmailField(
        required=True,
    )
    password = CharField(
        write_only=True,
        validators=[drf_validate_password],
    )

    def validate(self, attrs):
        request = self.context.get("request")
        user = authenticate(
            request=request,
            email=attrs["email"],
            password=attrs["password"],
        )

        if user is None:
            raise AuthenticationFailed("Invalid email or password")

        attrs["user"] = user
        return attrs


class LoginResponseSerializer(Serializer):
    profile = ProfileSerializer(read_only=True)  # type: ignore
    token = CharField(read_only=True)  # type: ignore
    expiry = DateTimeField(read_only=True)
