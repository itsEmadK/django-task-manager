from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer

from accounts.models import User


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "name",
            "age",
            "password",
        ]
        extra_kwargs = {
            "id": {
                "read_only": True,
            },
            "email": {
                "read_only": True,
            },
            "name": {
                "required": True,
            },
            "age": {
                "required": False,
            },
            "password": {
                "required": False,
                "write_only": True,
            },
        }

    def create(self, validated_data):
        raise ValidationError(
            "Registering users must be done through the register serializer"
        )

    def update(self, instance: User, validated_data: dict):
        password = validated_data.pop("password")
        instance.name = validated_data.get("name", instance.name)
        instance.age = validated_data.get("age", instance.age)
        if password:
            instance.set_password(password)
        instance.save()

        return instance


