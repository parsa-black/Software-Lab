from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

User = settings.AUTH_USER_MODEL


class CustomUser(AbstractUser):
    xp = models.IntegerField(default=0)


class Game(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    STATUS_CHOICES = [
        ('waiting', 'Waiting for opponent'),
        ('active', 'Game in progress'),
        ('finished', 'Game finished'),
    ]

    player1 = models.ForeignKey(User, related_name='games_as_player1', on_delete=models.CASCADE)
    player2 = models.ForeignKey(User, related_name='games_as_player2', on_delete=models.CASCADE, null=True, blank=True)

    word = models.CharField(max_length=100)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='waiting')

    score_player1 = models.IntegerField(default=0)
    score_player2 = models.IntegerField(default=0)

    current_turn = models.ForeignKey(User, related_name='games_current_turn', on_delete=models.SET_NULL, null=True, blank=True)
    winner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='games_won', on_delete=models.SET_NULL, null=True, blank=True)
    loser = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='games_lose', on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    game_end_time = models.DateTimeField(null=True, blank=True)

    double_guess_player1 = models.BooleanField(default=False)
    double_guess_player2 = models.BooleanField(default=False)

    double_guess_count_player1 = models.IntegerField(default=0)
    double_guess_count_player2 = models.IntegerField(default=0)

    def __str__(self):
        return f"Game #{self.id} - {self.status}"


class Guess(models.Model):
    game = models.ForeignKey(Game, related_name='guesses', on_delete=models.CASCADE)
    player = models.ForeignKey(User, on_delete=models.CASCADE)
    letter = models.CharField(max_length=1)
    is_correct = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)
    position = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.player.username} guessed '{self.letter}' ({'✔️' if self.is_correct else '❌'})"


class WordBank(models.Model):
    DIFFICULTY_CHOICES = (
        ('easy', 'آسان'),
        ('medium', 'متوسط'),
        ('hard', 'سخت'),
    )

    word = models.CharField(max_length=100)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)

    def __str__(self):
        return f"{self.word} ({self.difficulty})"


class GameHintUsage(models.Model):
    HINT_CHOICES = [
        ('reveal_letter', 'Reveal Random Letter'),
        ('letter_count', 'Letter Count'),
        ('double_guess', 'Double Guess'),
    ]

    game = models.ForeignKey('Game', on_delete=models.CASCADE, related_name='hints_used')
    player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hints_used')
    hint_type = models.CharField(max_length=20, choices=HINT_CHOICES)
    used_at = models.DateTimeField(auto_now_add=True)
    extra_data = models.CharField(max_length=255, blank=True, null=True)  #  letter_count

    def __str__(self):
        return f"{self.player.username} used {self.hint_type} in game {self.game.id}"
