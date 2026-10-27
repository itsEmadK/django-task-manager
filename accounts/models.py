from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models


class User(AbstractBaseUser):
    email = models.EmailField(primary_key=True)
    name = models.CharField(max_length=150, blank=False)
    age = models.PositiveSmallIntegerField(blank=False, default=18)
