from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


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
    winner = models.ForeignKey(User, related_name='games_won', on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Game #{self.id} - {self.status}"


class Guess(models.Model):
    game = models.ForeignKey(Game, related_name='guesses', on_delete=models.CASCADE)
    player = models.ForeignKey(User, on_delete=models.CASCADE)
    letter = models.CharField(max_length=1)
    is_correct = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.player.username} guessed '{self.letter}' ({'✔️' if self.is_correct else '❌'})"
