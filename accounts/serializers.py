from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from knox.models import AuthToken
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.exceptions import ValidationError as DrfValidationError
from rest_framework.fields import CharField, DateTimeField, EmailField, IntegerField
from rest_framework.fields import UUIDField
from rest_framework.generics import get_object_or_404
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

        return user


class RegisterResponseSerializer(Serializer):
    challenge_id = UUIDField(read_only=True)


class VerifyRegisterOTPRequestSerializer(Serializer):
    challenge_id = UUIDField(
        write_only=True,
        required=True,
    )
    code = IntegerField(
        write_only=True,
        required=True,
        min_value=100_000,
        max_value=999_999,
    )

    def validate(self, attrs):
        challenge_id = attrs["challenge_id"]
        otp_exists = OTP.objects.filter(challenge_id=challenge_id).exists()

        if not otp_exists:
            raise ValidationError("Challenge ID is invalid")

        otp: OTP = OTP.objects.get(challenge_id=challenge_id)
        code = attrs["code"]

        if not otp.check_code(plain_code=code):
            raise ValidationError("Code is invalid")

        attrs["otp"] = otp
        return attrs

    def save(self):
        otp = self.validated_data["otp"]

        user = User.objects.get(email=otp.email)
        user.email_verified = True
        user.save()
        token, token_key = AuthToken.objects.create(user=user)  # type: ignore

        return user, token.expiry, token_key


class VerifyRegisterOTPResponseSerializer(Serializer):
    user = UserSerializer(read_only=True)  # type: ignore
    token = CharField(read_only=True)
    token_expiry = DateTimeField(read_only=True)


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
