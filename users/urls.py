
from django.urls import path
from .views import LoginView, RegisterView, RefreshTokenView, LogoutView


urlpatterns = [
    path("login", LoginView.as_view()),
    path("register", RegisterView.as_view()),
    path("refresh", RefreshTokenView.as_view()),
    path("logout", LogoutView.as_view()),
]
