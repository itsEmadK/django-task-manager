from typing import Any

from django.core.management import BaseCommand

from accounts.models import User

DEFAULT_USERS = [
    {
        "name": "admin",
        "is_staff": True,
        "email": "admin@taskmgr.com",
        "password": "admin-pass",  # update later to use a value from .env
    },
    {
        "name": "emad",
        "is_staff": False,
        "email": "emadkheyroddin@gmail.com",
        "password": "good-password",  # update later to use a value from .env
    },
]


def seed_users():
    for user_info in DEFAULT_USERS:
        password = user_info.pop("password")
        user, created = User.objects.get_or_create(
            email=user_info["email"],
            defaults=user_info,
        )
        if created:
            user.set_password(password)
            user.save()


class Command(BaseCommand):
    help = "seeds default users"

    def handle(self, *args: Any, **options: Any) -> str | None:
        seed_users()
        self.stdout.write(self.style.SUCCESS("default users seeded successfully"))
