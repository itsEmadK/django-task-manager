from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.fields import IntegerField, SerializerMethodField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer

from tasks.models import Category, Project, Task


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


class ReadCategorySerializer(ModelSerializer):
    """Read-only serializer responsible for reading categories"""

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

        project_pk = attrs.get("project", getattr(self.instance, "project", None)).pk

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


class TaskSummarySerializer(ModelSerializer):
    """Used for compact task representation"""

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "category",
            "priority",
            "status",
            "due_date",
        ]


class ReadTaskSerializer(ModelSerializer):
    """Read-only serializer responsible for reading tasks

    If 'exclude_category' is set to True in the context, 'category' will
    be excluded from representation.
    """

    category = ReadCategorySerializer(read_only=True)  # type: ignore
    prerequisites = TaskSummarySerializer(
        read_only=True,  # type: ignore
        many=True,  # type: ignore
    )
    dependents = SerializerMethodField(read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "notes",
            "category",
            "priority",
            "status",
            "due_date",
            "dependents",
            "prerequisites",
        ]

    def get_dependents(self, obj):
        return TaskSummarySerializer(obj.dependents.all(), many=True).data  # type: ignore

    def get_fields(self):
        fields = super().get_fields()
        if self.context.get("exclude_category", False):
            fields.pop("category", None)  # type: ignore

        return fields

    def save(self):
        raise NotImplementedError("this serializer is read-only")


class WriteTaskSerializer(ModelSerializer):
    """Responsible for creating/updating tasks; requires 'user' in its context"""

    prerequisites = PrimaryKeyRelatedField(
        queryset=Task.objects.none(),
        many=True,
    )

    category = PrimaryKeyRelatedField(
        queryset=Category.objects.none(),
    )

    class Meta:
        model = Task
        fields = [
            "title",
            "notes",
            "category",
            "priority",
            "status",
            "due_date",
            "prerequisites",
        ]

    def get_fields(self):
        fields = super().get_fields()
        user = self.context["user"]

        # The condition is here just to quiet swagger
        if user and user.is_authenticated:
            fields["prerequisites"].queryset = Task.objects.filter(owner=user)  # type: ignore
            fields["category"].queryset = Category.objects.filter(owner=user)  # type: ignore
        else:
            fields["prerequisites"].queryset = Task.objects.none()  # type: ignore
            fields["category"].queryset = Category.objects.none()  # type: ignore

        return fields

    def validate_title(self, value):
        user = self.context["user"]
        same_title_exists = Task.objects.filter(
            owner=user,
            title__iexact=value,
        ).exists()

        if same_title_exists:
            raise ValidationError("this title has been used before")

        return value

    def validate_due_date(self, value):
        if value < timezone.now():
            raise ValidationError("due date must be in the future")

        return value

    def validate_prerequisites(self, value):
        instance = self.instance
        if instance and instance in value:
            raise ValidationError("a task can not be a prerequisite of itself")

        return value

    def save(self):
        user = self.context["user"]
        return super().save(owner=user)
