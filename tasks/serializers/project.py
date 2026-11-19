from rest_framework.fields import IntegerField
from rest_framework.serializers import ModelSerializer

from tasks.models import Project


class ProjectSerializer(ModelSerializer):
    """Responsible for reading and writing projects.
    \n Requires 'user' in the context if used for writing projects."""

    tasks_count = IntegerField(read_only=True)
    categories_count = IntegerField(read_only=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "description",
            "status",
            "priority",
            "tasks_count",
            "categories_count",
        ]

    def save(self):
        if self.instance:
            return super().save()
        else:
            user = self.context["user"]
            return super().save(owner=user)
