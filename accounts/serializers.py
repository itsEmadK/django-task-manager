from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.exceptions import ValidationError as DrfValidationError
from rest_framework.fields import CharField, DateTimeField, EmailField, UUIDField
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework.validators import UniqueValidator

from accounts.models import User
from otp.models import OTP


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
            "email_verified",
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
            "email_verified": {
                "read_only": True,
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
        otp_code, otp = OTP.objects.generate(user=user)

        return (user, otp, otp_code)


class RegisterResponseSerializer(Serializer):
    user = UserSerializer(read_only=True)  # type: ignore
    otp_challenge_id = UUIDField(read_only=True)


class LoginRequestSerializer(Serializer):
    email = EmailField(
        required=True,
    )

    def validate(self, attrs):
        user_exists = User.objects.filter(email=attrs["email"]).exists()

        if not user_exists:
            raise AuthenticationFailed("User does not exist")

        return attrs

    def save(self):
        user = User.objects.get(email=self.validated_data["email"])
        otp_code, otp = OTP.objects.generate(user=user)
        return user, otp_code, otp


class LoginResponseSerializer(Serializer):
     user = UserSerializer(read_only=True)  # type: ignore
     otp_challenge_id = UUIDField(read_only=True)
