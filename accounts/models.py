import secrets
from datetime import timedelta

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.hashers import make_password
from django.core.validators import (
    MaxValueValidator,
    MinLengthValidator,
    MinValueValidator,
)
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email: str, password: str):
        if email is None:
            raise ValueError("Email is required")

        user = self.model(email=self.normalize_email(email=email))
        user.set_password(password)
        user.save()
        return user

    def create_super_user(self, email: str, password: str):
        if email is None:
            raise ValueError("Email is required")

        user = self.model(
            email=self.normalize_email(email=email),
            is_staff=True,
        )
        user.set_password(password)
        user.save()
        return user


class User(AbstractBaseUser):
    email = models.EmailField(unique=True)
    name = models.CharField(
        max_length=150, blank=False, validators=[MinLengthValidator(3)]
    )
    age = models.PositiveSmallIntegerField(
        blank=True,
        default=18,
        validators=[MinValueValidator(18), MaxValueValidator(120)],
    )
    is_staff = models.BooleanField(default=False)
    email_verified = models.BooleanField(blank=True, default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"

    def is_email_verified(self):
        return self.email_verified

    def generate_otp(self, expiry: timedelta):
        code = str(secrets.randbelow(900_000) + 100_000)
        hashed = make_password(password=code)
        expires_at = timezone.now() + expiry
        OTP.objects.create(
            user=self,
            hashed_code=hashed,
            expires_at=expires_at,
        )
        return code


class OTP(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        blank=False,
    )
    code_hash = models.CharField(max_length=256, blank=False)
    expires_at = models.DateTimeField(blank=False)
    is_used = models.BooleanField(blank=True, default=False)
