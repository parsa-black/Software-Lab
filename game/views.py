# game/views.py
from django.db import models
from .models import Game, Guess
from .serializers import (RegisterSerializer, ProfileSerializer, GameCreateSerializer, AvailableGameSerializer,
                          GameStatusSerializer)
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, views
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

User = get_user_model()


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
        game.save()

        return Response({'detail': 'Join Successful.'}, status=status.HTTP_200_OK)


# Game Status
class GameStatusView(generics.RetrieveAPIView):
    queryset = Game.objects.all()
    serializer_class = GameStatusSerializer
    permission_classes = [permissions.IsAuthenticated]


# Guess View
class GuessLetterView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, game_id):
        user = request.user
        letter = request.data.get('letter', '').lower()
        game = get_object_or_404(Game, pk=game_id)

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
                game.score_player1 += 70
            else:
                game.score_player2 += 70
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

        # Award XP to winner based on difficulty
        if game.winner:
            if game.difficulty == 'easy':
                game.winner.xp += 30
            elif game.difficulty == 'medium':
                game.winner.xp += 50
            elif game.difficulty == 'hard':
                game.winner.xp += 100
            game.winner.save()

        # Award XP to loser based on difficulty
        if game.loser:
            if game.difficulty == 'easy':
                game.loser.xp += 10
            elif game.difficulty == 'medium':
                game.loser.xp += 16
            elif game.difficulty == 'hard':
                game.loser.xp += 33
            game.loser.save()

        # TODO: Check for time expiration (if you implement timing)

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
