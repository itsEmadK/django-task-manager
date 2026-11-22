from django.urls import path

from tasks.views import (
    CategoryDetailView,
    CategoryHistoryView,
    CategoryListView,
    CategoryTasksView,
    CreateTaskAttachmentView,
    DeleteCategoryTasksView,
    DeleteProjectCategoriesView,
    DeleteProjectTasksView,
    ProjectCategoriesView,
    ProjectDetailView,
    ProjectHistoryView,
    ProjectListView,
    ProjectTasksView,
    TaskAttachmentDetailView,
    TaskDependentsView,
    TaskDetailView,
    TaskHistoryView,
    TaskListView,
    TaskPrerequisitesView,
)

urlpatterns = [
    path("categories/", CategoryListView.as_view()),
    path("categories/<int:id>", CategoryDetailView.as_view()),
    path("categories/<int:id>/history", CategoryHistoryView.as_view()),
    path("categories/<int:category_id>/tasks", CategoryTasksView.as_view()),
    path(
        "categories/<int:category_id>/delete-tasks", DeleteCategoryTasksView.as_view()
    ),
    path("tasks/", TaskListView.as_view()),
    path("tasks/<int:id>/", TaskDetailView.as_view()),
    path("tasks/<int:id>/depdendents", TaskDependentsView.as_view()),
    path("tasks/<int:id>/prerequisites", TaskPrerequisitesView.as_view()),
    path("tasks/<int:id>/history", TaskHistoryView.as_view()),
    path("tasks/<int:task_id>/attachments", CreateTaskAttachmentView.as_view()),
    path(
        "tasks/<int:task_id>/attachments/<int:id>", TaskAttachmentDetailView.as_view()
    ),
    path("projects/", ProjectListView.as_view()),
    path("projects/<int:id>/", ProjectDetailView.as_view()),
    path("projects/<int:id>/history", ProjectHistoryView.as_view()),
    path("projects/<int:project_id>/categories", ProjectCategoriesView.as_view()),
    path(
        "projects/<int:project_id>/delete-categories",
        DeleteProjectCategoriesView.as_view(),
    ),
    path("projects/<int:project_id>/tasks", ProjectTasksView.as_view()),
    path(
        "projects/<int:project_id>/delete-tasks",
        DeleteProjectTasksView.as_view(),
    ),
]
