import secrets
import uuid  # noqa: I001

from django.contrib.auth.hashers import check_password, make_password
from datetime import timedelta
from django.db.models import BooleanField, CharField, DateTimeField, EmailField, Model
from django.db.models import Manager, UUIDField
from django.utils import timezone


from rest_framework.exceptions import ValidationError


class OTPManager(Manager):
    def generate(
        self,
        email,
        expiry: timedelta = timedelta(minutes=10),
    ):
        code = secrets.randbelow(999_999) + 100_000
        hashed = make_password(str(code))

        instance = OTP.objects.create(
            email=email,
            code_hash=hashed,
            expires_at=timezone.now() + expiry,
        )

        return instance, code


class OTP(Model):
    email = EmailField(blank=False)
    challenge_id = UUIDField(
        primary_key=True,
        default=uuid.uuid4,
    )
    code_hash = CharField(
        max_length=512,
        blank=False,
    )
    expires_at = DateTimeField(
        blank=False,
    )
    is_used = BooleanField(
        default=False,
    )

    objects = OTPManager()

    def is_expired(self):
        return timezone.now() >= self.expires_at

    def check_code(
        self,
        plain_code,
    ):
        valid = check_password(
            password=plain_code,
            encoded=self.code_hash,
        )
        return valid
