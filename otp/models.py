import secrets
import uuid
from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils import timezone

from accounts.models import User


class OTPManager(models.Manager):
    def generate(
        self,
        user: User,
        expiry: timedelta = timedelta(minutes=10),
    ):
        user.otp.delete()  # type: ignore

        code = secrets.randbelow(900_000) + 100_000
        hashed = make_password(password=str(code))
        expires_at = timezone.now() + expiry

        otp: OTP = OTP.objects.create(
            user=user,
            code_hash=hashed,
            expires_at=expires_at,
        )

        return code, otp


class OTP(models.Model):
    challenge_id = models.UUIDField(
        primary_key=True,
        editable=False,
        default=uuid.uuid4,
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="otp",
        related_query_name="otp",
        blank=False,
    )
    code_hash = models.CharField(max_length=256, blank=False)
    expires_at = models.DateTimeField(blank=False)
    is_used = models.BooleanField(default=False)

    objects = OTPManager()

    def check_code(self, plain_code):
        return check_password(
            password=plain_code,
            encoded=self.code_hash,
        )
