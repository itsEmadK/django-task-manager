from rest_framework.exceptions import ValidationError
from rest_framework.fields import IntegerField, SerializerMethodField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer

from tasks.models import Category, Task


class CategorySerializer(ModelSerializer):

    tasks_count = IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "tasks_count",
        ]


class TaskSummarySerializer(ModelSerializer):
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


class TaskSerializer(ModelSerializer):

    category = CategorySerializer(read_only=True)  # type: ignore
    category_id = PrimaryKeyRelatedField(
        write_only=True,
        queryset=Category.objects.all(),
        required=False,
        source="category",
    )

    prerequisites = SerializerMethodField(read_only=True)
    prerequisite_ids = PrimaryKeyRelatedField(
        queryset=Task.objects.all(),
        write_only=True,
        required=False,
        many=True,
        source="prerequisites",
    )

    dependents = SerializerMethodField(read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "notes",
            "category",
            "category_id",
            "priority",
            "status",
            "due_date",
            "dependents",
            "prerequisites",
            "prerequisite_ids",
        ]

    def get_prerequisites(self, obj):
        return TaskSummarySerializer(obj.prerequisites.all(), many=True).data  # type: ignore

    def get_dependents(self, obj):
        return TaskSummarySerializer(obj.dependents.all(), many=True).data  # type: ignore

    def validate(self, attrs):
        # TODO: make sure to later prevent circular dependencies

        prerequisites = attrs.get("prerequisites", [])

        if self.instance and self.instance in prerequisites:
            raise ValidationError("task can't depend on itself")

        return attrs

    def get_fields(self):
        fields = super().get_fields()

        user = self.context.get("user", None)

        # Just to get drf-spectacular off my back
        if user and user.is_authenticated:
            fields["prerequisite_ids"].queryset = Task.objects.filter(owner=user)  # type: ignore
            fields["category_id"].queryset = Category.objects.filter(owner=user)  # type: ignore
        else:
            fields["prerequisite_ids"].queryset = Task.objects.none()  # type: ignore
            fields["category_id"].queryset = Category.objects.none()  # type: ignore

        category_determined = self.context.get("category_determined", False)
        if category_determined:
            fields.pop("category_id")

        include_category = self.context.get("include_category", True)
        if not include_category:
            fields.pop("category")

        return fields
