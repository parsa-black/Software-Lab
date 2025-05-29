# game/urls.py
from django.urls import path
from .views import RegisterView, ProfileView, GameCreateView, AvailableGamesView, JoinGameView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('games/create/', GameCreateView.as_view(), name='game-create'),
    path('games/available/', AvailableGamesView.as_view(), name='available-games'),
    path('games/<int:pk>/join/', JoinGameView.as_view(), name='join-game'),
]
