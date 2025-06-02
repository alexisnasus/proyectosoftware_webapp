from rest_framework import serializers
from .models import Transaccion, Item
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

class ItemSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    descuento = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=0)


    
class TransaccionSerializer(serializers.ModelSerializer):
    items = ItemSerializer(source='item_set', many=True, read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    descuento_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_final = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

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

    
class AplicarDescuentoSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(choices=['porcentaje', 'monto_fijo'])
    valor = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    producto_id = serializers.CharField(required=False)
    
# DTO de entrada (inputCarrito)
class InputItemDTO(serializers.Serializer):
    codigo = serializers.CharField()
    cantidad = serializers.IntegerField(min_value=1)

# DTO de salida (outputCarrito)
class OutputItemDTO(serializers.Serializer):
    nombre = serializers.CharField()
    cantidad = serializers.IntegerField()
    estado = serializers.ChoiceField(choices=["CONFIRMADA", "FALLIDA"])