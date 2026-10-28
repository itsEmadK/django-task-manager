from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, EmailField
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework.validators import UniqueValidator

from accounts.models import User


class UserSerializer(ModelSerializer):
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
        raise ValidationError(
            "Registering users must be done through the register serializer"
        )

    def update(self, instance: User, validated_data: dict):
        password = validated_data.pop("password", None)
        instance.name = validated_data.get("name", instance.name)
        instance.age = validated_data.get("age", instance.age)
        if password:
            instance.set_password(password)
        instance.save()

        return instance


class RegisterRequestSerializer(Serializer):
    email = EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())],
    )
    password = CharField(
        write_only=True,
        min_length=12,
    )

    def save(self):
        email = self.validated_data.pop("email")
        password = self.validated_data.pop("password", None)

        if not password:
            raise ValidationError("password is required")

        user: User = User.objects.create_user(email=email, password=password)
        token = Token.objects.create(user=user)

        return (user, token)


class RegisterResponseSerializer(Serializer):
    user = UserSerializer(read_only=True)  # type: ignore
    token = CharField(read_only=True)  # type: ignore


class LoginRequestSerializer(Serializer):
    email = EmailField(
        required=True,
    )
    password = CharField(
        write_only=True,
        min_length=12,
    )


class LoginResponseSerializer(Serializer):
    user = UserSerializer(read_only=True)  # type: ignore
    token = CharField(read_only=True)  # type: ignore
