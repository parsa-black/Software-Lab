# game/serializers.py
from .models import Game
from django.contrib.auth.models import User
from rest_framework import serializers

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
