from django.db.models.query import QuerySet
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsOwner
from tasks.models import Category, Task
from tasks.serializers import CategorySerializer, TaskSerializer


class CategoryList(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CategorySerializer

    def get_queryset(self) -> QuerySet:
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


class TaskList(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TaskSerializer

    def get_queryset(self) -> QuerySet:
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
