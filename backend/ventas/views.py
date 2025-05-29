from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Producto, Stock, Item, Transaccion
from .serializers import (
    InputItemDTO,
    UserSerializer,
    MyTokenObtainPairSerializer,
    ProductoSerializer,
    StockSerializer,
)


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            token = RefreshToken(request.data["refresh"])
            token.blacklist()
            return Response({"detail": "Sesión cerrada correctamente"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({"error": "Token inválido o ausente"}, status=status.HTTP_400_BAD_REQUEST)


class ConcretarVentaAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        request_body=InputItemDTO(many=True),
        responses={
            200: "Transacción exitosa",
            400: "Error de validación",
            409: "Algunos productos sin stock suficiente",
        },
    )
    def post(self, request):
        input_items = request.data  # Asume lista directa

        if not input_items:
            return Response({"error": "Debe enviar la lista de items"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = InputItemDTO(data=input_items, many=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            transaccion = Transaccion.objects.create(estado='PENDIENTE')
            output_items = []
            all_confirmed = True

            for item_data in serializer.validated_data:
                codigo = item_data['codigo']
                cantidad = item_data['cantidad']

                try:
                    producto = Producto.objects.get(codigo=codigo)
                    stock = Stock.objects.select_for_update().get(producto=producto)

                    if stock.cantidad >= cantidad:
                        stock.cantidad -= cantidad
                        stock.save()
                        Item.objects.create(transaccion=transaccion, producto=producto, cantidad=cantidad)
                        output_items.append({"nombre": producto.nombre, "cantidad": cantidad, "estado": "CONFIRMADA"})
                    else:
                        all_confirmed = False
                        output_items.append({"nombre": producto.nombre, "cantidad": cantidad, "estado": "FALLIDA"})
                except Producto.DoesNotExist:
                    all_confirmed = False
                    output_items.append({"nombre": f"Producto con código {codigo} no encontrado", "cantidad": cantidad, "estado": "FALLIDA"})
                except Stock.DoesNotExist:
                    all_confirmed = False
                    output_items.append({"nombre": producto.nombre if 'producto' in locals() else codigo, "cantidad": cantidad, "estado": "FALLIDA"})

            transaccion.estado = 'CONFIRMADA' if all_confirmed else 'FALLIDA'
            transaccion.save()

        return Response({
            "transaccion_id": str(transaccion.id),
            "estado_transaccion": transaccion.estado,
            "items": output_items,
            "usuario": UserSerializer(request.user).data,
        }, status=status.HTTP_200_OK if all_confirmed else status.HTTP_409_CONFLICT)


class ProductoListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={200: ProductoSerializer(many=True)},
    )
    def get(self, request):
        productos = Producto.objects.all()
        serializer = ProductoSerializer(productos, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        request_body=ProductoSerializer,
        responses={201: ProductoSerializer},
    )
    def post(self, request):
        serializer = ProductoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductoDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={200: ProductoSerializer},
    )
    def get(self, request, pk):
        producto = get_object_or_404(Producto, pk=pk)
        serializer = ProductoSerializer(producto)
        return Response(serializer.data)

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        request_body=ProductoSerializer,
        responses={200: ProductoSerializer},
    )
    def put(self, request, pk):
        producto = get_object_or_404(Producto, pk=pk)
        serializer = ProductoSerializer(producto, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={204: 'No Content'},
    )
    def delete(self, request, pk):
        producto = get_object_or_404(Producto, pk=pk)
        producto.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class StockListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={200: 'Lista de stocks'},
    )
    def get(self, request):
        stocks = Stock.objects.all()
        serializer = StockSerializer(stocks, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        request_body=StockSerializer,
        responses={201: StockSerializer},
    )
    def post(self, request):
        serializer = StockSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StockDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={200: StockSerializer},
    )
    def get(self, request, pk):
        stock = get_object_or_404(Stock, pk=pk)
        serializer = StockSerializer(stock)
        return Response(serializer.data)

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        request_body=StockSerializer,
        responses={200: StockSerializer},
    )
    def put(self, request, pk):
        stock = get_object_or_404(Stock, pk=pk)
        serializer = StockSerializer(stock, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={204: 'No Content'},
    )
    def delete(self, request, pk):
        stock = get_object_or_404(Stock, pk=pk)
        stock.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
