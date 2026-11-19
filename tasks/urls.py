from django.urls import path

from tasks.views import (
    CategoryDetailView,
    CategoryListView,
    CategoryTasksView,
    DeleteCategoryTasksView,
    DeleteProjectCategoriesView,
    DeleteProjectTasksView,
    ProjectCategoriesView,
    ProjectDetailView,
    ProjectListView,
    ProjectTasksView,
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
    path("projects/", ProjectListView.as_view()),
    path("projects/<int:id>/", ProjectDetailView.as_view()),
    path("projects/<int:project_id>/categories", ProjectCategoriesView.as_view()),
    path(
        "projects/<int:project_id>/categories/delete-categories",
        DeleteProjectCategoriesView.as_view(),
    ),
    path("projects/<int:project_id>/tasks", ProjectTasksView.as_view()),
    path(
        "projects/<int:project_id>/delete-tasks",
        DeleteProjectTasksView.as_view(),
    ),
]
