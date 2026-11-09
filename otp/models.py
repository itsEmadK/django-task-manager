from django.db.models import (
    CASCADE,
    BooleanField,
    CharField,
    DateTimeField,
    Model,
    OneToOneField,
)

from accounts.models import User


class OTP(Model):
    user = OneToOneField(
        User,
        on_delete=CASCADE,
        blank=False,
    )
    code_hash = CharField(max_length=256, blank=False)
    expires_at = DateTimeField(blank=False)
    is_used = BooleanField(blank=True, default=False)
