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
    CurrentUser,
    Login,
    Logout,
    LogoutAll,
    RegisterUser,
    UserDetail,
    UserList,
)
from tasks.views import (
    CategoryDetail,
    CategoryList,
    CategoryTasks,
    DeleteCategoryTasks,
    TaskDetail,
    TaskList,
)

urlpatterns = [
    path("register/", RegisterUser.as_view()),
    path("login/", Login.as_view()),
    path("logout/", Logout.as_view()),
    path("logoutall/", LogoutAll.as_view()),
    path("me/", CurrentUser.as_view()),
    path("categories/", CategoryList.as_view()),
    path("categories/<int:id>", CategoryDetail.as_view()),
    path("categories/<int:category_id>/tasks", CategoryTasks.as_view()),
    path("categories/<int:category_id>/delete-tasks", DeleteCategoryTasks.as_view()),
    path("tasks/", TaskList.as_view()),
    path("tasks/<int:id>/", TaskDetail.as_view()),
    path("users/<int:id>/", UserDetail.as_view(), name="user_detail"),
    path("admin/users", UserList.as_view()),
    path("api/schema", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs", SpectacularSwaggerView.as_view(url_name="schema")),
]
