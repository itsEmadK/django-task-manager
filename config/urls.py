"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from accounts.views import (
    CurrentUserView,
    LoginView,
    LogoutView,
    LogoutAllView,
    RegisterUserView,
    UserDetailView,
    UserListView,
    VerifyRegisterOTPView,
)
from tasks.views import (
    CategoryDetailView,
    CategoryListView,
    CategoryTasksView,
    DeleteCategoryTasksView,
    TaskDetailView,
    TaskListView,
)

urlpatterns = [
    path("register/", RegisterUserView.as_view()),
    path("verify-email/", VerifyRegisterOTPView.as_view()),
    path("login/", LoginView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("logoutall/", LogoutAllView.as_view()),
    path("me/", CurrentUserView.as_view()),
    path("categories/", CategoryListView.as_view()),
    path("categories/<int:id>", CategoryDetailView.as_view()),
    path("categories/<int:category_id>/tasks", CategoryTasksView.as_view()),
    path(
        "categories/<int:category_id>/delete-tasks", DeleteCategoryTasksView.as_view()
    ),
    path("tasks/", TaskListView.as_view()),
    path("tasks/<int:id>/", TaskDetailView.as_view()),
    path("users/<int:id>/", UserDetailView.as_view(), name="user_detail"),
    path("admin/users", UserListView.as_view()),
    path("api/schema", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs", SpectacularSwaggerView.as_view(url_name="schema")),
]
