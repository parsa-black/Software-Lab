# game/views.py
from rest_framework import generics, permissions
from django.contrib.auth.models import User
from .serializers import RegisterSerializer, ProfileSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer


class ProfileView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user
