# game/views.py
from django.db import models
from rest_framework.exceptions import PermissionDenied

from .models import Game, Guess
from .serializers import (RegisterSerializer, ProfileSerializer, GameCreateSerializer, AvailableGameSerializer,
                          GameStatusSerializer, LeaderboardSerializer)
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, views
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from datetime import timedelta
from django.utils import timezone

User = get_user_model()


# Game Timer
def set_game_end_time(game):
    if game.difficulty == 'easy':
        duration = timedelta(minutes=10)
    elif game.difficulty == 'medium':
        duration = timedelta(minutes=7)
    elif game.difficulty == 'hard':
        duration = timedelta(minutes=5)
    else:
        duration = timedelta(minutes=10)

    game.game_end_time = timezone.now() + duration


# Player XP Award
def award_xp(game, winner, loser):
    if winner:
        if game.difficulty == 'easy':
            winner.xp += 30
        elif game.difficulty == 'medium':
            winner.xp += 50
        elif game.difficulty == 'hard':
            winner.xp += 100
        winner.save()

    if loser:
        if game.difficulty == 'easy':
            loser.xp += 10
        elif game.difficulty == 'medium':
            loser.xp += 16
        elif game.difficulty == 'hard':
            loser.xp += 33
        loser.save()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer


class ProfileView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user


# Create Game
class GameCreateView(generics.CreateAPIView):
    serializer_class = GameCreateSerializer
    permission_classes = [permissions.IsAuthenticated]


# Available Game
class AvailableGamesView(generics.ListAPIView):
    serializer_class = AvailableGameSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Game.objects.filter(player2__isnull=True, status='waiting')


# Game Join
class JoinGameView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        game = get_object_or_404(Game, pk=pk)

        if game.player2 is not None:
            return Response({'detail': 'Game Has Player Two.'}, status=status.HTTP_400_BAD_REQUEST)

        if game.player1 == request.user:
            return Response({'detail': 'You Are Player One.'}, status=status.HTTP_400_BAD_REQUEST)

        game.player2 = request.user
        game.status = 'active'
        set_game_end_time(game)
        game.save()

        return Response({'detail': 'Join Successful.'}, status=status.HTTP_200_OK)


# Game Status
class GameStatusView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GameStatusSerializer
    queryset = Game.objects.all()

    def get_object(self):
        game = super().get_object()

        if self.request.user != game.player1 and self.request.user != game.player2:
            raise PermissionDenied("You are not a player in this game.")

        return game


# Guess View
class GuessLetterView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, game_id):
        user = request.user
        letter = request.data.get('letter', '').lower()
        game = get_object_or_404(Game, pk=game_id)

        # Prevent non-players from guessing
        if user != game.player1 and user != game.player2:
            raise PermissionDenied("You are not a player in this game.")

        # Prevent guessing if the game hasn't started yet
        if game.status != 'active':
            return Response({"error": "The game has not started yet."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if game time is over
        if game.game_end_time and timezone.now() > game.game_end_time:
            if game.score_player1 > game.score_player2:
                game.winner = game.player1
                game.loser = game.player2
            elif game.score_player2 > game.score_player1:
                game.winner = game.player2
                game.loser = game.player1
            else:
                game.winner = None
                game.loser = None

            game.status = 'finished'
            award_xp(game, game.winner, game.loser)
            game.save()
            return Response({"error": "Time is over. Game finished."}, status=status.HTTP_400_BAD_REQUEST)

        # First Game Check
        if game.status == 'finished':
            return Response({"error": "Game already finished"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Validate letter input
        if not letter or len(letter) != 1 or not letter.isalpha():
            return Response({"error": "Invalid letter"}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Check if it's user's turn
        if game.current_turn != user:
            return Response({"error": "Not your turn"}, status=status.HTTP_403_FORBIDDEN)

        # 3. Check if letter already guessed
        if game.guesses.filter(letter__iexact=letter).exists():
            return Response({"error": "Letter already guessed"}, status=status.HTTP_400_BAD_REQUEST)

        # 4. Check if guess is correct
        is_correct = letter in game.word.lower()

        # 5. Update score
        if is_correct:
            if user == game.player1:
                game.score_player1 += 50
            else:
                game.score_player2 += 50
        else:
            if user == game.player1:
                game.score_player1 -= 10
            else:
                game.score_player2 -= 10

        # 6. Save guess
        Guess.objects.create(game=game, player=user, letter=letter, is_correct=is_correct)

        # 7. Switch turn
        if game.current_turn == game.player1:
            game.current_turn = game.player2
        else:
            game.current_turn = game.player1

        # 8. Check if game finished
        guessed_letters = game.guesses.filter(is_correct=True).values_list('letter', flat=True)
        if all(char.lower() in guessed_letters for char in game.word.lower()):
            game.status = 'finished'
            if game.score_player1 > game.score_player2:
                game.winner = game.player1
                game.loser = game.player2
            elif game.score_player2 > game.score_player1:
                game.winner = game.player2
                game.loser = game.player1
            else:
                game.winner = None  # Draw
                game.loser = None

        award_xp(game, game.winner, game.loser)
        game.save()

        # 9. Return updated game status
        serializer = GameStatusSerializer(game)
        return Response(serializer.data)


# User's Games History
class UserGamesListView(generics.ListAPIView):
    serializer_class = GameStatusSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        status_param = self.request.query_params.get('status')  # optional filter by status
        queryset = Game.objects.filter(
            models.Q(player1=user) | models.Q(player2=user)
        )
        if status_param in ['waiting', 'active', 'finished']:
            queryset = queryset.filter(status=status_param)
        return queryset.order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response({"message": "No Game History"}, status=status.HTTP_200_OK)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# Leader Board
class LeaderboardView(generics.ListAPIView):
    queryset = User.objects.order_by('-xp')[:10]
    serializer_class = LeaderboardSerializer
    permission_classes = []