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
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined']


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'password', 'password_confirm']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        return attrs

    def create(self, validated_data):
        # Remover password_confirm antes de crear el usuario
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        # Crear usuario
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=6)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'password']

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        
        # Actualizar campos normales
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Actualizar contraseña si se proporcionó
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Agregar información del usuario al token
        token['username'] = user.username
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['role'] = getattr(user, 'role', '')
        token['full_name'] = f"{user.first_name} {user.last_name}".strip() or user.username
        return token


# ------------------------------
# Serializer para Producto
# ------------------------------

class ProductoSerializer(serializers.ModelSerializer):
    # Campo extra que toma obj.stock.cantidad o 0 si no existe relación
    stock = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = ['id', 'codigo', 'nombre', 'precio', 'stock']  # agregamos el campo “stock”

    def get_stock(self, obj):
        # Si existe un registro de Stock para este Producto, devolvemos la cantidad; si no, 0
        try:
            return obj.stock.cantidad
        except Stock.DoesNotExist:
            return 0


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
