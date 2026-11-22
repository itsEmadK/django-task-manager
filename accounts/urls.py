from django.urls import path

from accounts.views import (
    CurrentUserProfileView,
    CurrentUserView,
    LoginView,
    LogoutAllView,
    LogoutView,
    ProfileHistoryView,
    RegisterUserView,
)

urlpatterns = [
    path("register/", RegisterUserView.as_view()),
    path("login/", LoginView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("logoutall/", LogoutAllView.as_view()),
    path("me/", CurrentUserView.as_view()),
    path("me/profile", CurrentUserProfileView.as_view()),
    path("me/profile/history", ProfileHistoryView.as_view()),
]
