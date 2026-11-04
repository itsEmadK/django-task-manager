from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from knox.models import AuthToken
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.exceptions import ValidationError as DrfValidationError
from rest_framework.fields import CharField, DateTimeField, EmailField
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework.validators import UniqueValidator

from accounts.models import User


def drf_validate_password(value):
    try:
        validate_password(value)
    except DjangoValidationError as e:
        raise DrfValidationError(e.messages)


class UserSerializer(ModelSerializer):
    password = CharField(write_only=True, validators=[drf_validate_password])

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "name",
            "age",
            "password",
        ]
        extra_kwargs = {
            "id": {
                "read_only": True,
            },
            "email": {
                "read_only": True,
            },
            "name": {
                "required": True,
            },
            "age": {
                "required": False,
            },
            "password": {
                "required": False,
                "write_only": True,
            },
        }

    def create(self, validated_data):
        raise DrfValidationError(
            "Registering users must be done through the register serializer"
        )

    def update(self, instance: User, validated_data: dict):
        password = validated_data.pop("password", None)
        if password:
            instance.set_password(password)

        instance.name = validated_data.get("name", instance.name)
        instance.age = validated_data.get("age", instance.age)

        instance.save()

        return instance


class RegisterRequestSerializer(Serializer):
    email = EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())],
    )
    password = CharField(write_only=True, validators=[drf_validate_password])

    def save(self):
        email = self.validated_data.pop("email")
        password = self.validated_data.pop("password", None)

        if not password:
            raise DrfValidationError("password is required")

        user: User = User.objects.create_user(email=email, password=password)
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
    user = UserSerializer(read_only=True)  # type: ignore
    token = CharField(read_only=True)  # type: ignore
    expiry = DateTimeField(read_only=True)
