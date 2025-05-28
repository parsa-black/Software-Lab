# game/views.py
from .models import Game
from rest_framework import generics, permissions
from django.contrib.auth.models import User
from .serializers import RegisterSerializer, ProfileSerializer, GameCreateSerializer, AvailableGameSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer


class ProfileView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user


class GameCreateView(generics.CreateAPIView):
    serializer_class = GameCreateSerializer
    permission_classes = [permissions.IsAuthenticated]


class AvailableGamesView(generics.ListAPIView):
    serializer_class = AvailableGameSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Game.objects.filter(player2__isnull=True, status='waiting')
