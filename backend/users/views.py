from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import MyTokenObtainPairSerializer

class MyTokenObtainPairView(TokenObtainPairView):
    """
    Vista para obtener pares de tokens (access + refresh)
    incluyendo el claim 'role' del usuario.
    """
    serializer_class = MyTokenObtainPairSerializer
