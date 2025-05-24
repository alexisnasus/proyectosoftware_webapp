from rest_framework import serializers
from .models import Producto, Stock

class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = ['id', 'codigo', 'nombre', 'precio']
        ref_name = 'InventarioProducto'


class StockSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)
    producto_id = serializers.PrimaryKeyRelatedField(
        queryset=Producto.objects.all(),
        source='producto',
        write_only=True
    )

    class Meta:
        model = Stock
        fields = ['producto', 'producto_id', 'cantidad']
        ref_name = 'InventarioStock'
