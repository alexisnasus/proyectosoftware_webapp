from rest_framework import serializers
from .models import Producto, Stock

class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        db_table = 'producto'
        model = Producto
        fields = ['id', 'codigo', 'nombre', 'precio']
        ref_name = 'InventarioProducto'


class StockSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)

    class Meta:
        db_table = 'stock'
        model = Stock
        fields = ['producto', 'cantidad']
