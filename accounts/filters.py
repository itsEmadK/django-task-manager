import django_filters

from accounts.models import User


class UserFilter(django_filters.FilterSet):
    class Meta:
        model = User
        fields = {
            "name": [
                "exact",
                "icontains",
            ],
            "age": [
                "lte",
                "gte",
            ],
            "is_staff": [
                "exact",
            ],
            "email": [
                "exact",
                "icontains",
            ],
        }
