from django.contrib.auth.base_user import AbstractBaseUser
from django.core.validators import (
    MaxValueValidator,
    MinLengthValidator,
    MinValueValidator,
)
from django.db import models


class User(AbstractBaseUser):
    email = models.EmailField(primary_key=True)
    name = models.CharField(
        max_length=150, blank=False, validators=[MinLengthValidator(3)]
    )
    age = models.PositiveSmallIntegerField(
        blank=True,
        default=18,
        validators=[MinValueValidator(18), MaxValueValidator(120)],
    )

    USERNAME_FIELD = "email"
