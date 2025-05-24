from rest_framework import serializers
from inventario.models import Producto  # usa el modelo compartido
from .models import Transaccion, Item

from inventario.serializers import ProductoSerializer  # usa el serializer oficial

class ItemSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        db_table = 'item'
        model = Item
        fields = ['producto', 'cantidad', 'subtotal']

class TransaccionSerializer(serializers.ModelSerializer):
    items = ItemSerializer(source='item_set', many=True, read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        db_table = 'transaccion'
        model = Transaccion
        fields = ['id', 'creado_en', 'confirmado_en', 'estado', 'items', 'total']
