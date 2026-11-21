from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.core import validators
from django.db import models
from django.db.models.functions import Lower


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
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                name="unique_email_per_user",
            )
        ]


class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        related_query_name="profile",
    )
    name = models.CharField(
        max_length=150,
        validators=[validators.MinLengthValidator(3)],
    )
    age = models.PositiveSmallIntegerField(
        validators=[
            validators.MinValueValidator(18),
            validators.MaxValueValidator(120),
        ],
    )
    avatar = models.ImageField(
        null=True,
        upload_to="avatars",
    )
