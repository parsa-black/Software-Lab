# game/serializers.py
from .models import Game, Guess
from django.contrib.auth import get_user_model
from rest_framework import serializers
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
        fields = ('id', 'username', 'email')


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
            'easy': ['book', 'tree', 'lamp'],
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
    winner = serializers.CharField(source='winner.username', read_only=True)
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

    def get_word_progress(self, obj):
        # Collect all guessed letters for this game
        guessed_letters = obj.guesses.values_list('letter', flat=True)
        # Replace un guessed letters with underscores
        return ' '.join([letter if letter.lower() in guessed_letters else '_' for letter in obj.word])

    def get_remaining_time(self, obj):
        # Optional: Implement logic for countdown timer per difficulty if needed
        return None
