from rest_framework import serializers
from inventario.models import Producto
from inventario.serializers import ProductoSerializer
from .models import Transaccion, Item

class ItemSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    descuento = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=0)

    class Meta:
        model = Item
        fields = ['producto', 'cantidad', 'descuento', 'subtotal']

class TransaccionSerializer(serializers.ModelSerializer):
    items = ItemSerializer(source='item_set', many=True, read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    descuento_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_final = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Transaccion
        fields = ['id', 'creado_en', 'confirmado_en', 'estado', 'items', 'total', 'descuento_total', 'total_final']

class AplicarDescuentoSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(choices=['porcentaje', 'monto_fijo'])
    valor = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    producto_id = serializers.CharField(required=False)