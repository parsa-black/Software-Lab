# game/serializers.py
from .models import Game, Guess
from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.utils import timezone

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'xp')


# Game Serializer
class GameCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = ('id', 'difficulty')

    def create(self, validated_data):
        # Choice Random Word for Difficulty
        difficulty = validated_data['difficulty']
        word = self._get_random_word(difficulty)
        user = self.context['request'].user

        game = Game.objects.create(
            player1=user,
            word=word,
            difficulty=difficulty,
            current_turn=user  # Start With Player One
        )
        return game

    def _get_random_word(self, difficulty):
        # Test Word For Now
        word_pool = {
            'easy': ['book', 'tree'],
            'medium': ['planet', 'banana', 'laptop'],
            'hard': ['electricity', 'vocabulary', 'microphone']
        }
        from random import choice
        return choice(word_pool[difficulty])


class AvailableGameSerializer(serializers.ModelSerializer):
    player1 = serializers.StringRelatedField()  # Show Player One Username

    class Meta:
        model = Game
        fields = ('id', 'player1', 'difficulty', 'created_at')


# Game Status
class GameStatusSerializer(serializers.ModelSerializer):
    player1 = serializers.CharField(source='player1.username', read_only=True)
    player2 = serializers.CharField(source='player2.username', read_only=True)
    winner = serializers.SerializerMethodField()
    current_turn = serializers.CharField(source='current_turn.username', read_only=True)
    word_progress = serializers.SerializerMethodField()
    remaining_time = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = [
            'id', 'player1', 'player2', 'difficulty', 'status',
            'score_player1', 'score_player2', 'current_turn',
            'word_progress', 'remaining_time', 'created_at', 'winner'
        ]

    def get_winner(self, obj):
        if obj.winner is None:
            return "Draw"
        return obj.winner.username

    def get_word_progress(self, obj):
        correct_guesses = obj.guesses.filter(is_correct=True)
        revealed_positions = {
            guess.position: guess.letter.lower()
            for guess in correct_guesses
        }
        display = [
            revealed_positions.get(i, '_') for i in range(len(obj.word))
        ]
        return ' '.join(display)

    def get_remaining_time(self, obj):
        if obj.game_end_time:
            remaining = obj.game_end_time - timezone.now()
            if remaining.total_seconds() > 0:
                return int(remaining.total_seconds())
        return 0


# Leader Board
class LeaderboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'xp']