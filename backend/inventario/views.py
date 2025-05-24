from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Producto, Stock
from .serializers import ProductoSerializer, StockSerializer
from drf_yasg.utils import swagger_auto_schema

# CRUD de productos
class ProductoView(APIView):
    @swagger_auto_schema(request_body=ProductoSerializer)
    def post(self, request):
        serializer = ProductoSerializer(data=request.data)
        if serializer.is_valid():
            producto = serializer.save()
            Stock.objects.create(producto=producto)  # crea stock vacío
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        productos = Producto.objects.all()
        serializer = ProductoSerializer(productos, many=True)
        return Response(serializer.data)

# Obtener, actualizar y eliminar productos
class ProductoDetalleView(APIView):
    def get(self, request, pk):
        producto = get_object_or_404(Producto, pk=pk)
        serializer = ProductoSerializer(producto)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=ProductoSerializer)
    def put(self, request, pk):
        producto = get_object_or_404(Producto, pk=pk)
        serializer = ProductoSerializer(producto, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        producto = get_object_or_404(Producto, pk=pk)
        producto.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# Gestión de stock
class StockView(APIView):
    def get(self, request):
        stocks = Stock.objects.select_related('producto').all()
        serializer = StockSerializer(stocks, many=True)
        return Response(serializer.data)

    def post(self, request):
        producto_id = request.data.get('producto_id')
        cantidad = int(request.data.get('cantidad', 0))

        try:
            stock = Stock.objects.get(producto_id=producto_id)
            stock.cantidad += cantidad
            stock.save()
            return Response({'mensaje': 'Stock actualizado'}, status=200)
        except Stock.DoesNotExist:
            return Response({'error': 'Producto sin stock asociado'}, status=404)
