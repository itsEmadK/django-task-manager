from rest_framework.exceptions import ValidationError
from rest_framework.fields import IntegerField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer

from tasks.models import Category, Project
from tasks.serializers.project import ProjectSerializer


class ReadCategorySerializer(ModelSerializer):
    """Read-only serializer responsible for reading categories

    Accepts an 'exclude_fields' str array in the context. Fields present in
    this array will be excluded from the serializer representation
    """

    tasks_count = IntegerField(required=False)
    project = ProjectSerializer()

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "project",
            "tasks_count",
        ]

    def get_fields(self):
        exclude_fields = self.context.get("exclude_fields", [])
        fields = super().get_fields()
        for field in exclude_fields:
            fields.pop(field, None)

        return fields

    def save(self):
        raise NotImplementedError("this serializer is read-only")


class WriteCategorySerializer(ModelSerializer):
    """Responsible for creating/updating categories; requires 'user' in its context"""

    project = PrimaryKeyRelatedField(
        queryset=Project.objects.none(),
        required=False,
    )

    class Meta:
        model = Category
        fields = [
            "name",
            "project",
        ]

    def get_fields(self):
        fields = super().get_fields()
        user = self.context["user"]
        if user and user.is_authenticated:
            fields["project"].queryset = Project.objects.filter(owner=user)  # type: ignore
        else:
            fields["project"].queryset = Project.objects.none()  # type: ignore

        return fields

    def validate(self, attrs):
        user = self.context["user"]
        name = attrs.get("name", getattr(self.instance, "name", None))
        queryset = Category.objects.filter(owner=user, name__iexact=name)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        project = attrs.get("project", getattr(self.instance, "project", None))
        project_pk = getattr(project, "pk", None)

        if (
            project_pk
            and queryset.filter(
                project__pk=project_pk,  # type: ignore
            ).exists()
        ):
            raise ValidationError(
                "this category name has already been used in this project"
            )

        if queryset.filter(project__isnull=True).exists():
            raise ValidationError("this category name has already been used")

        return attrs

    def save(self):
        user = self.context["user"]
        return super().save(owner=user)
