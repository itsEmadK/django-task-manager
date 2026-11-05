from django.db.models.query import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    get_object_or_404,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsOwner
from tasks.models import Category, Task
from tasks.serializers import CategorySerializer, TaskSerializer


class CategoryList(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CategorySerializer
    filter_backends = [SearchFilter]
    search_fields = ["name"]

    def get_queryset(self) -> QuerySet:
        if getattr(self, "swagger_fake_view", False):
            return Category.objects.none()

        return Category.objects.filter(owner=self.request.user)

    def perform_create(self, serializer) -> None:
        serializer.save(owner=self.request.user)


class CategoryDetail(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = CategorySerializer
    lookup_url_kwarg = "id"
    lookup_field = "pk"

    def get_queryset(self) -> QuerySet:
        return Category.objects.filter(owner=self.request.user)


class DeleteCategoryTasks(APIView):
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


class TaskList(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TaskSerializer
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["title", "notes"]
    filterset_fields = {
        "due_date": ["exact", "lte", "gte"],
        "priority": ["exact"],
        "status": ["exact"],
    }

    def get_queryset(self) -> QuerySet:
        # Just so drf-spectacular can find the filters
        if getattr(self, "swagger_fake_view", False):
            return Task.objects.none()

        return Task.objects.filter(owner=self.request.user)

    def perform_create(self, serializer) -> None:
        serializer.save(owner=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user  # type: ignore

        return context


class TaskDetail(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsOwner]
    owner_field = "owner"
    serializer_class = TaskSerializer
    lookup_url_kwarg = "id"
    lookup_field = "pk"

    def get_queryset(self) -> QuerySet:
        return Task.objects.filter(owner=self.request.user)


class CategoryTasks(ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["title", "notes"]
    filterset_fields = {
        "due_date": ["exact", "lte", "gte"],
        "priority": ["exact"],
        "status": ["exact"],
    }

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

    def perform_create(self, serializer) -> None:
        category = self.get_category()
        serializer.save(owner=self.request.user, category=category)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["category_determined"] = True  # type: ignore
        context["include_category"] = False  # type: ignore
        return context
