from django.db.models import Count
from django.db.models.query import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    get_object_or_404,
)
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsOwner
from tasks.models import Category, Project, Task, TaskAttachment
from tasks.serializers.category import (
    ReadCategorySerializer,
    ReadProjectCategorySerializer,
    WriteCategorySerializer,
)
from tasks.serializers.project import ProjectSerializer
from tasks.serializers.task import (
    ReadProjectTaskSerializer,
    ReadTaskAttachmentSerializer,
    ReadTaskSerializer,
    WriteTaskAttachmentSerializer,
    WriteTaskSerializer,
)


class CategoryListView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name"]
    ordering_fields = [
        "id",
        "name",
        "tasks_count",
    ]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ReadCategorySerializer
        else:
            return WriteCategorySerializer

    def get_queryset(self) -> QuerySet:
        if getattr(self, "swagger_fake_view", False):
            return Category.objects.none()

        return Category.objects.filter(owner=self.request.user).annotate(
            tasks_count=Count("task", distinct=True)
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user  # type: ignore
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        response_serializer = ReadCategorySerializer(
            instance=serializer.instance,  # type: ignore
            context=self.get_serializer_context(),  # type: ignore
        )

        return Response(data=response_serializer.data)


class CategoryDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsOwner]
    lookup_url_kwarg = "id"
    lookup_field = "pk"

    def get_queryset(self) -> QuerySet:
        return Category.objects.filter(owner=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ReadCategorySerializer
        else:
            return WriteCategorySerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user  # type: ignore
        return context

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        serializer = self.get_serializer(
            instance=instance,
            data=request.data,
            partial=partial,
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        response_serializer = ReadCategorySerializer(
            instance=serializer.instance,  # type: ignore
            context=self.get_serializer_context(),  # type: ignore
        )

        return Response(data=response_serializer.data)


class DeleteCategoryTasksView(APIView):
    permission_classes = [IsAuthenticated]

    def get_category(self, category_id):
        category = get_object_or_404(
            queryset=Category.objects.filter(owner=self.request.user),
            id=category_id,
        )
        return category

    def delete(self, request, category_id):
        category = self.get_category(category_id)
        num_deleted, _ = category.tasks.all().delete()
        return Response(data={"deleted_tasks_count": num_deleted})


class TaskListView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    search_fields = ["title", "notes"]
    filterset_fields = {
        "due_date": ["exact", "lte", "gte"],
        "priority": ["exact"],
        "status": ["exact"],
    }
    ordering_fields = [
        "id",
        "title",
        "due_date",
        "priority",
        "status",
        "category",
    ]

    def get_queryset(self) -> QuerySet:
        # Just so drf-spectacular can find the filters
        if getattr(self, "swagger_fake_view", False):
            return Task.objects.none()

        return Task.objects.select_related("category").filter(owner=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ReadTaskSerializer
        else:
            return WriteTaskSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user  # type: ignore

        return context

    def create(self, request):
        serializer = self.get_serializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        response_serializer = ReadTaskSerializer(
            instance=serializer.instance,  # type: ignore
            context=self.get_serializer_context(),  # type: ignore
        )

        return Response(data=response_serializer.data)


class TaskDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsOwner]
    lookup_url_kwarg = "id"
    lookup_field = "pk"

    def get_queryset(self) -> QuerySet:
        return Task.objects.filter(owner=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ReadTaskSerializer
        else:
            return WriteTaskSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["user"] = self.request.user  # type: ignore
        return ctx

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        serializer = self.get_serializer(
            instance=instance,
            data=request.data,
            partial=partial,
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        response_serializer = ReadTaskSerializer(
            instance=serializer.instance,  # type: ignore
            context=self.get_serializer_context(),  # type: ignore
        )

        return Response(data=response_serializer.data)


class CategoryTasksView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    search_fields = ["title", "notes"]
    filterset_fields = {
        "due_date": ["exact", "lte", "gte"],
        "priority": ["exact"],
        "status": ["exact"],
    }
    ordering_fields = [
        "id",
        "title",
        "due_date",
        "priority",
        "status",
    ]

    def get_category(self):
        category_id = self.kwargs["category_id"]
        category = get_object_or_404(
            queryset=Category.objects.filter(owner=self.request.user),
            id=category_id,
        )
        return category

    def get_queryset(self) -> QuerySet:
        # Just so drf-spectacular can find the filters
        if getattr(self, "swagger_fake_view", False):
            return Task.objects.none()

        category = self.get_category()
        return Task.objects.filter(category=category)

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ReadTaskSerializer
        else:
            return WriteTaskSerializer

    def create(self, request, category_id):
        data = request.data
        category = self.get_category()
        data["category"] = category.pk
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        response_serializer = ReadTaskSerializer(
            instance=serializer.instance,  # type: ignore
            context=self.get_serializer_context(),  # type: ignore
        )

        return Response(data=response_serializer.data)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user  # type: ignore

        if self.request.method == "GET":
            context["exclude_fields"] = ["category"]  # type: ignore
        return context


class ProjectListView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProjectSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        "name",
        "description",
    ]
    ordering_fields = [
        "id",
        "name",
        "priority",
        "status",
        "tasks_count",
    ]

    def get_queryset(self) -> QuerySet:
        if getattr(self, "swagger_fake_view", False):
            return Project.objects.none()

        return (
            Project.objects.filter(owner=self.request.user)
            .annotate(tasks_count=Count("task", distinct=True))
            .annotate(categories_count=Count("category", distinct=True))
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user  # type: ignore
        return context


class ProjectDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = ProjectSerializer
    lookup_url_kwarg = "id"
    lookup_field = "pk"

    def get_queryset(self) -> QuerySet:
        return Project.objects.filter(owner=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user  # type: ignore
        return context


class ProjectCategoriesView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name"]
    ordering_fields = [
        "id",
        "name",
        "tasks_count",
    ]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ReadProjectCategorySerializer
        else:
            return WriteCategorySerializer

    def get_project(self):
        project_id = self.kwargs["project_id"]
        project = get_object_or_404(
            queryset=Project.objects.filter(owner=self.request.user),
            pk=project_id,
        )
        return project

    def get_queryset(self):
        project = self.get_project()
        return Category.objects.filter(
            owner=self.request.user,
            project=project,
        ).annotate(tasks_count=Count("task", distinct=True))

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user  # type: ignore
        return context

    def create(self, request, project_id):
        data = request.data
        project = self.get_project()
        data["project"] = project.pk
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        response_serializer = ReadProjectCategorySerializer(
            instance=serializer.instance,  # type: ignore
            context=self.get_serializer_context(),  # type: ignore
        )

        return Response(data=response_serializer.data)


class DeleteProjectCategoriesView(APIView):
    permission_classes = [IsAuthenticated]

    def get_project(self, project_id):
        project = get_object_or_404(
            queryset=Project.objects.filter(owner=self.request.user),
            id=project_id,
        )
        return project

    def delete(self, request, project_id):
        project = self.get_project(project_id)
        num_deleted, _ = project.categories.all().delete()
        return Response(data={"deleted_categories_count": num_deleted})


class ProjectTasksView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    search_fields = ["title", "notes"]
    filterset_fields = {
        "due_date": ["exact", "lte", "gte"],
        "priority": ["exact"],
        "status": ["exact"],
    }
    ordering_fields = [
        "id",
        "title",
        "due_date",
        "priority",
        "status",
    ]

    def get_project(self):
        project_id = self.kwargs["project_id"]
        project = get_object_or_404(
            queryset=Project.objects.filter(owner=self.request.user),
            pk=project_id,
        )
        return project

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ReadProjectTaskSerializer
        else:
            return WriteTaskSerializer

    def get_queryset(self):
        project = self.get_project()
        return Task.objects.filter(
            owner=self.request.user,
            project=project,
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user  # type: ignore
        if self.request.method == "GET":
            context["exclude_fields"] = ["project"]  # type: ignore

        return context

    def create(self, request, project_id):
        data = request.data
        project = self.get_project()
        data["project"] = project.pk
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        response_serializer = ReadProjectTaskSerializer(
            instance=serializer.instance,  # type: ignore
            context=self.get_serializer_context(),  # type: ignore
        )

        return Response(data=response_serializer.data)


class DeleteProjectTasksView(APIView):
    permission_classes = [IsAuthenticated]

    def get_project(self, project_id):
        project = get_object_or_404(
            queryset=Project.objects.filter(owner=self.request.user),
            id=project_id,
        )
        return project

    def delete(self, request, project_id):
        project = self.get_project(project_id)
        num_deleted, _ = project.tasks.all().delete()
        return Response(data={"deleted_tasks_count": num_deleted})


class CreateTaskAttachmentView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def get_task(self, task_id):
        return get_object_or_404(
            queryset=Task.objects.filter(owner=self.request.user),
            pk=task_id,
        )

    @extend_schema(
        request=WriteTaskAttachmentSerializer,
        responses=[ReadTaskAttachmentSerializer],
    )
    def post(self, request, task_id):
        task = self.get_task(task_id)
        serializer = WriteTaskAttachmentSerializer(
            data=request.data,  # type: ignore
            context={  # type: ignore
                "task": task,
            },
        )
        serializer.is_valid(raise_exception=True)
        attachment = serializer.save()

        return Response(
            data=ReadTaskAttachmentSerializer(
                instance=attachment,  # type: ignore
                context={"request": request},  # type: ignore
            ).data,
            status=status.HTTP_201_CREATED,
        )


class TaskAttachmentDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]
    lookup_url_kwarg = "id"
    lookup_field = "pk"

    def get_task(self):
        task_id = self.kwargs["task_id"]
        return get_object_or_404(
            queryset=Task.objects.filter(owner=self.request.user),
            pk=task_id,
        )

    def get_queryset(self):
        return TaskAttachment.objects.filter(task=self.get_task())

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ReadTaskAttachmentSerializer
        else:
            return WriteTaskAttachmentSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user  # type: ignore
        context["task"] = self.get_task()  # type: ignore
        return context

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        serializer = self.get_serializer(
            instance=instance,
            data=request.data,
            partial=partial,
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        response_serializer = ReadTaskAttachmentSerializer(
            instance=serializer.instance,  # type: ignore
            context=self.get_serializer_context(),  # type: ignore
        )

        return Response(data=response_serializer.data)
