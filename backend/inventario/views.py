from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from django.shortcuts import get_object_or_404
from .models import Producto, Stock
from drf_yasg import openapi
from .serializers import ProductoSerializer, StockSerializer
from .services import agregar_stock, quitar_stock

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
        
    @swagger_auto_schema(
        operation_description="Agrega cantidad al stock de un producto",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['producto_id', 'cantidad'],
            properties={
                'producto_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'cantidad': openapi.Schema(type=openapi.TYPE_INTEGER, minimum=1),
            },
        ),
        responses={200: StockSerializer, 400: "Error de validación", 404: "Producto no encontrado"}
    )
    @action(detail=False, methods=['post'], url_path='agregar')
    def agregar_stock(self, request):
        try:
            producto_id = request.data['producto_id']
            cantidad = int(request.data['cantidad'])
            
            stock = agregar_stock(producto_id, cantidad)
            serializer = StockSerializer(stock)
            
            return Response({
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except KeyError as e:
            return Response(
                {'error': f'Falta el campo requerido: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Stock.DoesNotExist:
            return Response(
                {'error': 'Producto no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

    @swagger_auto_schema(
        operation_description="Quita cantidad del stock de un producto",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['producto_id', 'cantidad'],
            properties={
                'producto_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'cantidad': openapi.Schema(type=openapi.TYPE_INTEGER, minimum=1),
            },
        ),
        responses={200: StockSerializer, 400: "Error de validación", 404: "Producto no encontrado"}
    )
    @action(detail=False, methods=['post'], url_path='quitar')
    def quitar_stock(self, request):
        try:
            producto_id = request.data['producto_id']
            cantidad = int(request.data['cantidad'])
            
            stock = quitar_stock(producto_id, cantidad)
            serializer = StockSerializer(stock)
            
            return Response({
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except KeyError as e:
            return Response(
                {'error': f'Falta el campo requerido: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Stock.DoesNotExist:
            return Response(
                {'error': 'Producto no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )