# /backend/ventas/serializers.py

from rest_framework import serializers
from .models import Transaccion, Item, Producto, Stock
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

# ------------------------------
# Serializers de autenticación (sin cambios)
# ------------------------------

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role']


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = getattr(user, 'role', '')
        return token


# ------------------------------
# Serializer para Producto
# ------------------------------

class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__'


# ------------------------------
# Serializer para Stock
# ------------------------------

class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = '__all__'


# ------------------------------
# DTO para cada ítem que viene en el "inputTransaccion"
# ------------------------------
class InputItemDTO(serializers.Serializer):
    codigo = serializers.CharField()
    cantidad = serializers.IntegerField(min_value=1)


# ------------------------------
# DTO para la creación de la Transacción (antes "carrito")
# ------------------------------
class InputTransaccionSerializer(serializers.Serializer):
    descuento_carrito = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0
    )
    items = InputItemDTO(many=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Debe enviar al menos un ítem en la Transacción.")
        return value


# ------------------------------
# Serializer que muestra cada ítem en la respuesta (nombre, cantidad y estado)
# ------------------------------
class OutputItemDTO(serializers.Serializer):
    nombre = serializers.CharField()
    cantidad = serializers.IntegerField()
    estado = serializers.ChoiceField(choices=["PENDIENTE", "CONFIRMADA", "FALLIDA"])


# ------------------------------
# Serializer para detalle de Transacción
# (incluye items, totales y descuento global)
# ------------------------------
class TransaccionDetailSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    descuento_carrito = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_final = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Transaccion
        fields = [
            'id',
            'creado_en',
            'confirmado_en',
            'estado',
            'descuento_carrito',
            'total',
            'total_final',
            'items',
        ]

    def get_items(self, obj):
        """
        Convertir cada Item en la respuesta: { nombre, cantidad, estado }.
        Estado en este punto se corresponde con Transaccion.estado:
        Si la transacción está PENDIENTE, todos los ítems salen "PENDIENTE".
        Si está CONFIRMADA/FALLIDA, todos los ítems heredan ese mismo estado.
        """
        estado_global = obj.estado
        resultado = []
        for item in obj.item_set.all():
            resultado.append({
                'nombre': item.producto.nombre,
                'cantidad': item.cantidad,
                'estado': estado_global
            })
        return resultado
