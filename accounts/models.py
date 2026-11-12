from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.core.validators import (
    MaxValueValidator,
    MinLengthValidator,
    MinValueValidator,
)
from django.db import models


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
    email_verified = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
