import mimetypes

from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer

from tasks.models import Category, Project, Task, TaskAttachment
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


class ReadTaskAttachmentSerializer(ModelSerializer):
    url = SerializerMethodField()
    file_size = SerializerMethodField()
    file_type = SerializerMethodField()
    file_name = SerializerMethodField()

    class Meta:
        model = TaskAttachment
        fields = [
            "id",
            "type",
            "url",
            "title",
            "notes",
            "order",
            "file_type",
            "file_size",
            "file_name",
        ]

    def get_url(self, obj):
        return obj.url or self.context["request"].build_absolute_uri(obj.file.url)

    def get_file_size(self, obj):
        if obj.file:
            return obj.file.size
        else:
            return None

    def get_file_type(self, obj):
        if obj.file:
            return mimetypes.guess_type(obj.file.name)[0]
        else:
            return None

    def get_file_name(self, obj):
        if obj.file:
            return obj.file.name
        else:
            return None

    def save(self):
        raise NotImplementedError("this serializer is read-only")


class WriteTaskAttachmentSerializer(ModelSerializer):
    """Requires 'task' in the serializer context"""

    class Meta:
        model = TaskAttachment
        fields = [
            "type",
            "url",
            "file",
            "title",
            "notes",
            "order",
        ]
        extra_kwargs = {
            "file": {
                "required": False,
            },
            "url": {
                "required": False,
            },
        }

    def validate(self, attrs):
        type = attrs.get("type", None)
        file = attrs.get("file", None)
        url = attrs.get("url", None)

        if type == "file":
            if not file:
                raise ValidationError("file must be present for file attachments")
            if url:
                raise ValidationError("can't pass external url to a file attachment")
        elif type == "external_url":
            if not url:
                raise ValidationError(
                    "url must be present for external url attachments"
                )
            if file:
                raise ValidationError("can't pass file to an external url attachment")

        return attrs

    def save(self):
        task = self.context["task"]
        data = self.validated_data
        if data["type"] == "file":
            data["url"] = None
            if data["file"] and self.instance:
                self.instance.file.delete()
        elif data["type"] == "external_url":
            data["file"] = None
            if self.instance:
                self.instance.file.delete()

        return super().save(**data, task=task)


class ReadTaskSerializer(ModelSerializer):
    """Read-only serializer responsible for reading tasks"""

    category = ReadCategorySerializer()
    project = ProjectSerializer()
    prerequisites = TaskSummarySerializer(
        read_only=True,  # type: ignore
        many=True,  # type: ignore
    )
    dependents = SerializerMethodField(read_only=True)
    attachments = ReadTaskAttachmentSerializer(many=True)  # type: ignore

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
        project_pk = getattr(project, "pk", None)

        if (
            project_pk
            and queryset.filter(
                project__pk=project_pk,  # type: ignore
            ).exists()
        ):
            raise ValidationError(
                "this task title has already been used in this project"
            )

        if project:
            category = attrs.get("category")
            if category and not project.categories.filter(pk=category.pk).exists():
                raise ValidationError("this category isn't available in this project")

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
