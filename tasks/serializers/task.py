from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer

from tasks.models import Category, Project, Task
from tasks.serializers.attachment import ReadAttachmentSerializer
from tasks.serializers.category import (
    ReadCategorySerializer,
    ReadProjectCategorySerializer,
)
from tasks.serializers.project import ProjectSerializer


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
    """Read-only serializer responsible for reading tasks"""

    category = ReadCategorySerializer()
    project = ProjectSerializer()
    prerequisites = TaskSummarySerializer(
        read_only=True,  # type: ignore
        many=True,  # type: ignore
    )
    dependents = SerializerMethodField()
    attachments = ReadAttachmentSerializer(many=True)  # type: ignore

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "notes",
            "project",
            "category",
            "priority",
            "status",
            "due_date",
            "dependents",
            "prerequisites",
            "attachments",
        ]

    def get_dependents(self, obj):
        return TaskSummarySerializer(obj.dependents.all(), many=True).data  # type: ignore

    def save(self):
        raise NotImplementedError("this serializer is read-only")


class WriteTaskSerializer(ModelSerializer):
    """Responsible for creating/updating tasks; requires 'user' in its context"""

    prerequisites = PrimaryKeyRelatedField(
        queryset=Task.objects.none(),
        many=True,
    )
    project = PrimaryKeyRelatedField(
        queryset=Project.objects.none(),
        required=False,
    )
    category = PrimaryKeyRelatedField(
        queryset=Category.objects.none(),
        required=False,
    )

    class Meta:
        model = Task
        fields = [
            "title",
            "notes",
            "category",
            "project",
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
            fields["project"].queryset = Project.objects.filter(owner=user)  # type: ignore
            fields["prerequisites"].queryset = Task.objects.filter(owner=user)  # type: ignore
            fields["category"].queryset = Category.objects.filter(owner=user)  # type: ignore
        else:
            fields["project"].queryset = Project.objects.none()  # type: ignore
            fields["prerequisites"].queryset = Task.objects.none()  # type: ignore
            fields["category"].queryset = Category.objects.none()  # type: ignore

        return fields

    def validate_due_date(self, value):
        if value < timezone.now():
            raise ValidationError("due date must be in the future")

        return value

    def validate_prerequisites(self, value):
        instance = self.instance
        if instance and instance in value:
            raise ValidationError("a task can not be a prerequisite of itself")

        return value

    def validate(self, attrs):
        user = self.context["user"]
        title = attrs.get("title", getattr(self.instance, "title", None))
        queryset = Task.objects.filter(owner=user, title__iexact=title)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        project = attrs.get("project", getattr(self.instance, "project", None))
        category = attrs.get("category", getattr(self.instance, "project", None))

        if (
            project
            and queryset.filter(
                project=project,
            ).exists()
        ):
            raise ValidationError(
                "this task title has already been used in this project"
            )

        if project:
            if category and not project.categories.filter(pk=category.pk).exists():
                raise ValidationError("this category isn't available in this project")
        else:
            if category and category.project:
                if not project:
                    raise ValidationError(
                        "this category belongs to a project and can't be used for tasks without a project"
                    )

        if not project and queryset.filter(project__isnull=True).exists():
            raise ValidationError("this task title has already been used")

        return attrs

    def save(self):
        user = self.context["user"]
        return super().save(owner=user)


class ReadCategoryTaskSerializer(ReadTaskSerializer):

    def get_fields(self):
        fields = super().get_fields()
        fields.pop("category", None)
        return fields


class ReadProjectTaskSerializer(ReadTaskSerializer):

    category = ReadProjectCategorySerializer()

    def get_fields(self):
        fields = super().get_fields()
        fields.pop("project", None)
        return fields


class ReadTaskHistorySerializer(ModelSerializer):
    class Meta:
        model = Task.history.model  # type: ignore
        fields = [
            "title",
            "notes",
            "due_date",
            "priority",
            "status",
            "project",
            "category",
            "history_date",
            "history_type",
            "history_change_reason",
        ]

    def save(self):
        raise NotImplementedError("this is a read-only serializer")
