from rest_framework import generics, permissions

from .models import User
from .serializers import RegistroSerializer, UsuarioSerializer


class RegistroView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegistroSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveAPIView):
    serializer_class = UsuarioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
