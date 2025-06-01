# game/urls.py
from django.urls import path
from .views import (RegisterView, ProfileView, GameCreateView, AvailableGamesView, JoinGameView, GameStatusView,
                    GuessLetterView, UserGamesListView, LeaderboardView, RevealRandomLetterHintView,
                    LetterCountHintView, DoubleGuessHintView)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('games/create/', GameCreateView.as_view(), name='game-create'),
    path('games/available/', AvailableGamesView.as_view(), name='available-games'),
    path('games/<int:pk>/join/', JoinGameView.as_view(), name='join-game'),
    path('games/<int:pk>/status/', GameStatusView.as_view(), name='game-status'),
    path('games/<int:game_id>/guess/', GuessLetterView.as_view(), name='guess-letter'),
    path('games/<int:game_id>/hint/reveal-letter', RevealRandomLetterHintView.as_view(), name='RandomLetterHint'),
    path('games/<int:game_id>/hint/double-guess', DoubleGuessHintView.as_view(), name='DoubleGuessHint'),
    path('games/<int:game_id>/hint/letter-frequency', LetterCountHintView.as_view(), name='LetterCountHint'),
    path('games/', UserGamesListView.as_view(), name='user-games-list'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
]
