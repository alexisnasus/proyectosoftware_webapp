from rest_framework import serializers
from .models import Producto, Transaccion, LineaVenta

class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = ['codigo','nombre','precio']

class LineaVentaSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = LineaVenta
        fields = ['producto','cantidad','subtotal']

class TransaccionSerializer(serializers.ModelSerializer):
    lineas = LineaVentaSerializer(source='lineaventa_set', many=True, read_only=True)
    total  = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model  = Transaccion
        fields = ['id','creado_en','confirmado_en','estado','lineas','total']
