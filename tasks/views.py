from django.db.models import Count
from django.db.models.query import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    get_object_or_404,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsOwner
from tasks.models import Category, Project, Task
from tasks.serializers.category import ReadCategorySerializer, WriteCategorySerializer
from tasks.serializers.project import ProjectSerializer
from tasks.serializers.task import ReadTaskSerializer, WriteTaskSerializer


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
            tasks_count=Count("task")
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
            context["exclude_category"] = True  # type: ignore
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
            .annotate(tasks_count=Count("task"))
            .annotate(categories_count=Count("category"))
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user  # type: ignore
        return context
