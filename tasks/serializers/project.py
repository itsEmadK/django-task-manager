from rest_framework.exceptions import ValidationError
from rest_framework.fields import IntegerField
from rest_framework.serializers import ModelSerializer

from tasks.models import Project


class ProjectSerializer(ModelSerializer):
    """Responsible for reading and writing projects.
    \n Requires 'user' in the context if used for writing projects."""

    tasks_count = IntegerField(read_only=True, required=False)
    categories_count = IntegerField(read_only=True, required=False)

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

    def validate_name(self, value):
        user = self.context["user"]
        queryset = Project.objects.filter(owner=user)

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.filter(name__iexact=value).exists():
            raise ValidationError("this project name has been used before")

        return value


class ReadProjectHistorySerializer(ModelSerializer):
    class Meta:
        model = Project.history.model  # type: ignore
        fields = [
            "name",
            "description",
            "priority",
            "status",
            "deadline",
            "history_date",
            "history_type",
            "history_change_reason",
        ]

    def save(self):
        raise NotImplementedError("this is a read-only serializer")
