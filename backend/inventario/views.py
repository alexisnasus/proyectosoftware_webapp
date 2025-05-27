from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from django.shortcuts import get_object_or_404
from .models import Producto, Stock
from .services import actualizar_stock
from .serializers import ProductoSerializer, StockSerializer
from drf_yasg import openapi

class ProductoViewSet(viewsets.ViewSet):

    @action(detail=False, methods=['get'], url_path='listar')
    def listar(self, request):
        productos = Producto.objects.all()
        serializer = ProductoSerializer(productos, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=ProductoSerializer)
    @action(detail=False, methods=['post'], url_path='crear')
    def crear(self, request):
        serializer = ProductoSerializer(data=request.data)
        if serializer.is_valid():
            producto = serializer.save()
            Stock.objects.create(producto=producto)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='leer')
    def leer(self, request, pk=None):
        producto = get_object_or_404(Producto, pk=pk)
        serializer = ProductoSerializer(producto)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=ProductoSerializer)
    @action(detail=True, methods=['put'], url_path='actualizar')
    def actualizar(self, request, pk=None):
        producto = get_object_or_404(Producto, pk=pk)
        serializer = ProductoSerializer(producto, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], url_path='eliminar')
    def eliminar(self, request, pk=None):
        producto = get_object_or_404(Producto, pk=pk)
        producto.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class StockViewSet(viewsets.ViewSet):

    @action(detail=False, methods=['get'], url_path='listar')
    def listar(self, request):
        stocks = Stock.objects.select_related('producto').all()
        serializer = StockSerializer(stocks, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=StockSerializer)
    @action(detail=False, methods=['post'], url_path='crear')
    def crear(self, request):
        producto_id = request.data.get('producto_id')
        cantidad = int(request.data.get('cantidad', 0))
        try:
            stock = Stock.objects.get(producto_id=producto_id)
            stock.cantidad += cantidad
            stock.save()
            return Response({'mensaje': 'Stock actualizado'}, status=200)
        except Stock.DoesNotExist:
            return Response({'error': 'Producto sin stock asociado'}, status=404)
        


class StockViewSet(viewsets.ViewSet):

    @action(detail=False, methods=['get'], url_path='listar')
    def listar(self, request):
        stocks = Stock.objects.select_related('producto').all()
        serializer = StockSerializer(stocks, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=StockSerializer)
    @action(detail=False, methods=['post'], url_path='crear')
    def crear(self, request):
        producto_id = request.data.get('producto_id')
        try:
            cantidad = int(request.data.get('cantidad', 0))
        except (TypeError, ValueError):
            return Response({'error': 'Cantidad inválida'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            stock = Stock.objects.get(producto_id=producto_id)
            stock.cantidad += cantidad
            stock.save()
            return Response({'mensaje': 'Stock actualizado'}, status=status.HTTP_200_OK)
        except Stock.DoesNotExist:
            return Response({'error': 'Producto sin stock asociado'}, status=status.HTTP_404_NOT_FOUND)


    queryset = Stock.objects.select_related('producto')
    serializer_class = StockSerializer
    

    @swagger_auto_schema(request_body=StockSerializer)
    @action(detail=False, methods=['post'], url_path='agregar-o-quitar-productos')
    def modificar_stock(self, request):
        producto_id = request.data.get('producto_id')
        try:
            cantidad = int(request.data.get('cantidad', 0))
        except (TypeError, ValueError):
            return Response({'error': 'Cantidad inválida'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            stock = actualizar_stock(
                producto_id=producto_id,
                cantidad_alfa=cantidad
            )
            
            return Response({
                'mensaje': 'Stock modificado',
                'nuevo_stock': stock.cantidad,
                'alerta': stock.cantidad == 0
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)