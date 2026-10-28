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

    objects = UserManager()

    USERNAME_FIELD = "email"
