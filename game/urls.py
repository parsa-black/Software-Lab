# game/urls.py
from django.urls import path
from .views import RegisterView, ProfileView, GameCreateView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('games/create/', GameCreateView.as_view(), name='game-create'),
]
