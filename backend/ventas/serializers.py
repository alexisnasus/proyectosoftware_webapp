from rest_framework import serializers
from .models import Producto, Item, Stock
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = getattr(user, 'role', '')
        return token

# Producto Serializer para CRUD
class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__'  # o lista explícita de campos que quieres exponer

# Item Serializer para CRUD
class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'  # o lista explícita de campos

class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = '__all__'

# DTO de entrada (inputCarrito)
class InputItemDTO(serializers.Serializer):
    codigo = serializers.CharField()
    cantidad = serializers.IntegerField(min_value=1)

# DTO de salida (outputCarrito)
class OutputItemDTO(serializers.Serializer):
    nombre = serializers.CharField()
    cantidad = serializers.IntegerField()
    estado = serializers.ChoiceField(choices=["CONFIRMADA", "FALLIDA"])
