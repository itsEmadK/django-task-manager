from typing import Any

from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, DateTimeField, IntegerField, UUIDField
from rest_framework.generics import get_object_or_404
from rest_framework.serializers import Serializer

from accounts.serializers import UserSerializer
from otp.models import OTP


class VerifyEmailOTPRequestSerializer(Serializer):
    code = IntegerField(
        min_value=100000,
        max_value=999999,
        required=True,
    )
    challenge_id = UUIDField(
        required=True,
    )

    def validate(self, attrs: Any) -> Any:
        attrs = super().validate(attrs)

        code = attrs["code"]
        challenge_id = attrs["challenge_id"]

        otp: OTP = get_object_or_404(
            queryset=OTP.objects.filter(is_used=False),
            challenge_id=challenge_id,
        )

        if not otp.check_code(plain_code=code):
            raise ValidationError("OTP code is invalid")

        if otp.expires_at <= timezone.now():
            raise ValidationError("OTP code is expired")

        attrs["otp"] = otp

        return attrs

    def save(self):
        otp = self.validated_data.get("otp")
        otp.is_used = True
        otp.save()
        return otp


class VerifyEmailOTPResponseSerializer(Serializer):
    user = UserSerializer(read_only=True)  # type: ignore
    token = CharField(read_only=True)
    expiry = DateTimeField(read_only=True)
