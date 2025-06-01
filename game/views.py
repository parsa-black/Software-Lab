# game/views.py
import random

from django.db import models
from rest_framework.exceptions import PermissionDenied

from .models import Game, Guess, GameHintUsage
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
import re

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
        position = request.data.get('position')

        game = get_object_or_404(Game, pk=game_id)
        word = game.word.lower()

        # 1. Check if game time is over
        if game.game_end_time and timezone.now() > game.game_end_time:
            game.status = 'finished'
            if game.score_player1 > game.score_player2:
                game.winner, game.loser = game.player1, game.player2
            elif game.score_player2 > game.score_player1:
                game.winner, game.loser = game.player2, game.player1
            else:
                game.winner = game.loser = None
            award_xp(game, game.winner, game.loser)
            game.save()
            return Response({"error": "Time is over. Game finished."}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Game must be active
        if user != game.player1 and user != game.player2:
            raise PermissionDenied("You are not a player in this game.")

        if game.status == 'finished':
            return Response({"error": "Game already finished"}, status=status.HTTP_400_BAD_REQUEST)

        if game.status != 'active':
            return Response({"error": "The game has not started yet."}, status=status.HTTP_400_BAD_REQUEST)

        if game.current_turn != user:
            return Response({"error": "Not your turn"}, status=status.HTTP_403_FORBIDDEN)

        if not letter or len(letter) != 1 or not re.match(r'^[\u0600-\u06FF]$', letter):
            return Response({"error": "Invalid letter. Only Persian letters are allowed."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            position = int(position)
        except (TypeError, ValueError):
            return Response({"error": "Invalid position"}, status=status.HTTP_400_BAD_REQUEST)

        if position < 0 or position >= len(word):
            return Response({"error": "Position out of range"}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Only block if position was already correctly guessed
        if game.guesses.filter(position=position, is_correct=True).exists():
            return Response({"error": f"Position {position} already correctly guessed"}, status=status.HTTP_400_BAD_REQUEST)
        if game.guesses.filter(position=position, letter__iexact=letter).exists():
            return Response({"error": f"You already guessed letter '{letter}' at position {position}."},
                            status=status.HTTP_400_BAD_REQUEST)

        # 4. Check correctness only at that position
        is_correct = word[position] == letter

        # 5. Update score
        if is_correct:
            if user == game.player1:
                game.score_player1 += 80
            else:
                game.score_player2 += 80
        else:
            if user == game.player1:
                game.score_player1 -= 10
            else:
                game.score_player2 -= 10

        # 6. Save guess
        Guess.objects.create(game=game, player=user, letter=letter, position=position, is_correct=is_correct)

        # 7. Switch turn
        if user == game.player1:
            if game.double_guess_player1:
                game.double_guess_count_player1 += 1
                if game.double_guess_count_player1 >= 2:
                    game.double_guess_player1 = False
                    game.double_guess_count_player1 = 0
                    game.current_turn = game.player2
                else:
                    pass
            else:
                game.current_turn = game.player2
                game.double_guess_count_player1 = 0

        elif user == game.player2:
            if game.double_guess_player2:
                game.double_guess_count_player2 += 1
                if game.double_guess_count_player2 >= 2:
                    game.double_guess_player2 = False
                    game.double_guess_count_player2 = 0
                    game.current_turn = game.player1
                else:
                    pass
            else:
                game.current_turn = game.player1
                game.double_guess_count_player2 = 0

        # 8. Check if all positions correctly guessed
        correct_positions = set(game.guesses.filter(is_correct=True).values_list('position', flat=True))
        if correct_positions == set(range(len(word))):
            game.status = 'finished'

            player1_correct_count = game.guesses.filter(player=game.player1, is_correct=True).count()
            player2_correct_count = game.guesses.filter(player=game.player2, is_correct=True).count()

            if player1_correct_count > player2_correct_count:
                game.winner = game.player1
                game.loser = game.player2
            elif player2_correct_count > player1_correct_count:
                game.winner = game.player2
                game.loser = game.player1
            else:
                game.winner = game.loser = None

            award_xp(game, game.winner, game.loser)

        game.save()

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
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LeaderboardSerializer

    def get_queryset(self):
        return User.objects.filter(is_staff=False, is_superuser=False).order_by('-xp')[:10]


class RevealRandomLetterHintView(APIView):
    permission_classes = [permissions.IsAuthenticated]


    def post(self, request, game_id):
        game = get_object_or_404(Game, pk=game_id)
        user = request.user
        word = game.word.lower()

        if game.status != 'active':
            return Response({"error": "Game is not active."}, status=400)

        if user != game.player1 and user != game.player2:
            raise PermissionDenied("You are not a player in this game.")

        if game.current_turn != user:
            return Response({"error": "Not your turn."}, status=403)

        cost = 160
        if (user == game.player1 and game.score_player1 < cost) or \
           (user == game.player2 and game.score_player2 < cost):
            return Response({"error": "Not enough score to use this hint."}, status=400)

        guessed_positions = set(game.guesses.filter(is_correct=True).values_list('position', flat=True))
        available_positions = [i for i in range(len(word)) if i not in guessed_positions]

        if not available_positions:
            return Response({"error": "All letters already guessed."}, status=400)

        position = random.choice(available_positions)
        letter = word[position]

        Guess.objects.create(game=game, player=user, letter=letter, position=position, is_correct=True)

        if user == game.player1:
            game.score_player1 -= cost
            player1_correct_count = game.guesses.filter(player=game.player1, is_correct=True).count()
        else:
            game.score_player2 -= cost
            player2_correct_count = game.guesses.filter(player=game.player2, is_correct=True).count()

        game.current_turn = game.player2 if user == game.player1 else game.player1
        GameHintUsage.objects.create(game=game, player=user, hint_type='reveal_letter', extra_data=str(position))
        game.save()
        serializer = GameStatusSerializer(game)
        return Response(serializer.data)


class DoubleGuessHintView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, game_id):
        game = get_object_or_404(Game, pk=game_id)
        user = request.user
        cost = 100

        if user != game.player1 and user != game.player2:
            raise PermissionDenied("You are not a player in this game.")

        if game.status != 'active':
            return Response({"error": "Game is not active."}, status=400)

        if game.current_turn != user:
            return Response({"error": "Not your turn."}, status=403)

        if user == game.player1 and game.score_player1 < cost:
            return Response({"error": "Not enough score to use this hint."}, status=400)
        elif user == game.player2 and game.score_player2 < cost:
            return Response({"error": "Not enough score to use this hint."}, status=400)

        request.session['double_guess_active_for'] = game.id

        if user == game.player1:
            game.score_player1 -= cost
            game.double_guess_player1 = True
        else:
            game.score_player2 -= cost
            game.double_guess_player2 = True

        GameHintUsage.objects.create(game=game, player=user, hint_type='double_guess')
        game.save()
        return Response({"message": "You can now guess twice in this turn."})


class LetterCountHintView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, game_id):
        game = get_object_or_404(Game, pk=game_id)
        user = request.user
        letter = request.data.get('letter', '').strip().lower()
        word = game.word.lower()

        cost = 60

        if game.status != 'active':
            return Response({"error": "Game is not active."}, status=400)

        if not letter or len(letter) != 1 or not re.match(r'^[\u0600-\u06FF]$', letter):
            return Response({"error": "Enter a valid Persian letter."}, status=400)

        if (user == game.player1 and game.score_player1 < cost) or \
           (user == game.player2 and game.score_player2 < cost):
            return Response({"error": "Not enough score to use this hint."}, status=400)

        count = word.count(letter)

        if user == game.player1:
            game.score_player1 -= cost
        else:
            game.score_player2 -= cost

        # Log Hint Letter
        GameHintUsage.objects.create(game=game, player=user, hint_type='letter_count', extra_data=letter)

        game.save()
        return Response({
            "hint_type": "letter_count",
            "letter": letter,
            "count": count,
            "score_spent": cost
        })

