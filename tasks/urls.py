from django.urls import path

from tasks.views import (
    CategoryDetailView,
    CategoryListView,
    CategoryTasksView,
    DeleteCategoryTasksView,
    TaskDetailView,
    TaskListView,
)

urlpatterns = [
    path("categories/", CategoryListView.as_view()),
    path("categories/<int:id>", CategoryDetailView.as_view()),
    path("categories/<int:category_id>/tasks", CategoryTasksView.as_view()),
    path(
        "categories/<int:category_id>/delete-tasks", DeleteCategoryTasksView.as_view()
    ),
    path("tasks/", TaskListView.as_view()),
    path("tasks/<int:id>/", TaskDetailView.as_view()),
]
