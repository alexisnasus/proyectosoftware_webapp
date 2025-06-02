# /backend/ventas/views.py

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
    InputTransaccionSerializer,
    OutputItemDTO,
    TransaccionDetailSerializer,
    ProductoSerializer,
    StockSerializer,
    UserSerializer,
    MyTokenObtainPairSerializer,
)


# ------------------------------
# Vistas de autenticación (sin cambios)
# ------------------------------
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


# ------------------------------
# 1) Crear Transacción con lista de Ítems y descuento global
# ------------------------------
class TransaccionCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=InputTransaccionSerializer,
        responses={
            201: TransaccionDetailSerializer,
            400: "Error de validación"
        }
    )
    def post(self, request):
        """
        Crea una nueva Transacción (estado=PENDIENTE), crea todos los Item asociados
        y guarda el descuento global en Transaccion.descuento_carrito.
        """
        serializer = InputTransaccionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        datos = serializer.validated_data
        descuento_carrito = datos['descuento_carrito']
        items_data = datos['items']

        # 1) Crear la Transaccion en estado PENDIENTE
        transaccion = Transaccion.objects.create(
            estado='PENDIENTE',
            descuento_carrito=descuento_carrito
        )

        # 2) Por cada item entrante, buscar el producto por código y crear el Item
        errores = []
        creados = []
        for elemento in items_data:
            codigo = elemento['codigo']
            cantidad = elemento['cantidad']
            try:
                producto = Producto.objects.get(codigo=codigo)
            except Producto.DoesNotExist:
                errores.append(f"Producto con código '{codigo}' no encontrado.")
                continue

            item = Item.objects.create(
                transaccion=transaccion,
                producto=producto,
                cantidad=cantidad
            )
            creados.append(item)

        if errores:
            # Si alguno de los códigos no se encontró, eliminamos la transacción completa para no
            # dejar datos huérfanos en BD, y devolvemos 400 con los errores.
            transaccion.delete()
            return Response(
                {"errors": errores},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3) Si todo se creó bien, devolvemos el detalle completo de la transacción:
        detalle = TransaccionDetailSerializer(transaccion)
        return Response(detalle.data, status=status.HTTP_201_CREATED)


# ------------------------------
# 2) Obtener detalle de Transacción
# ------------------------------
class TransaccionDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={200: TransaccionDetailSerializer, 404: "Transacción no encontrada"}
    )
    def get(self, request, pk: int):
        transaccion = get_object_or_404(Transaccion, pk=pk)
        serializer = TransaccionDetailSerializer(transaccion)
        return Response(serializer.data)


# ------------------------------
# 3) Confirmar Transacción: verificar stock y descontar
# ------------------------------
class ConfirmarTransaccionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={
            200: "Transacción confirmada",
            400: "Error de validación",
            404: "Transacción no existe",
            409: "Stock insuficiente en alguno de los productos"
        }
    )
    def post(self, request, pk):
        """
        Verifica stock para cada ítem de la transacción (que debe estar PENDIENTE),
        descuenta si hay suficiente y cambia estado a CONFIRMADA o FALLIDA.
        Devuelve, para cada ítem, su nombre, cantidad y “estado” (allá).
        """
        transaccion = get_object_or_404(Transaccion, pk=pk)

        if transaccion.estado != 'PENDIENTE':
            return Response(
                {"error": "La transacción ya fue confirmada o está fallida."},
                status=status.HTTP_400_BAD_REQUEST
            )

        items = transaccion.item_set.select_related('producto').all()
        if not items.exists():
            return Response(
                {"error": "La transacción no tiene ítems para confirmar."},
                status=status.HTTP_400_BAD_REQUEST
            )

        output_items = []
        with transaction.atomic():
            # --- 1) Verificar stock de todos los ítems (sin descartar nada todavía) ---
            faltantes = []
            for item in items:
                try:
                    stock = Stock.objects.select_for_update().get(producto=item.producto)
                except Stock.DoesNotExist:
                    faltantes.append((item, "Sin registro de stock"))
                    continue

                if stock.cantidad < item.cantidad:
                    faltantes.append((item, "Stock insuficiente"))

            # --- 2) Si existe al menos un ítem con stock insuficiente, marcamos FALLIDA ---
            if faltantes:
                transaccion.estado = 'FALLIDA'
                transaccion.confirmado_en = None
                transaccion.save()

                # Construir output_items: todos los ítems salen en estado “FALLIDA”
                for item in items:
                    output_items.append({
                        "nombre": item.producto.nombre,
                        "cantidad": item.cantidad,
                        "estado": "FALLIDA"
                    })

                return Response(
                    {
                        "transaccion_id": str(transaccion.id),
                        "estado_transaccion": transaccion.estado,
                        "descuento_carrito": transaccion.descuento_carrito,
                        "items": output_items
                    },
                    status=status.HTTP_409_CONFLICT
                )

            # --- 3) Si todos los ítems tienen stock suficiente, se descuentan cantidades ---
            for item in items:
                stock = Stock.objects.select_for_update().get(producto=item.producto)
                stock.cantidad -= item.cantidad
                stock.save()
                output_items.append({
                    "nombre": item.producto.nombre,
                    "cantidad": item.cantidad,
                    "estado": "CONFIRMADA"
                })

            transaccion.estado = 'CONFIRMADA'
            transaccion.confirmado_en = None  # Si deseas dejar fecha: timezone.now()
            transaccion.save()

        # --- 4) Responder con los datos finales ---
        return Response(
            {
                "transaccion_id": str(transaccion.id),
                "estado_transaccion": transaccion.estado,
                "descuento_carrito": transaccion.descuento_carrito,
                "items": output_items
            },
            status=status.HTTP_200_OK
        )


# ------------------------------
# CRUD de Productos
# ------------------------------
class ProductoListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={200: ProductoSerializer(many=True)}
    )
    def get(self, request):
        productos = Producto.objects.all()
        serializer = ProductoSerializer(productos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        request_body=ProductoSerializer,
        responses={201: ProductoSerializer, 400: "Error de validación"}
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
        responses={200: ProductoSerializer, 404: "Producto no encontrado"}
    )
    def get(self, request, pk):
        producto = get_object_or_404(Producto, pk=pk)
        serializer = ProductoSerializer(producto)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        request_body=ProductoSerializer,
        responses={200: ProductoSerializer, 400: "Error de validación", 404: "Producto no encontrado"}
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
        responses={204: 'No Content', 404: "Producto no encontrado"}
    )
    def delete(self, request, pk):
        producto = get_object_or_404(Producto, pk=pk)
        producto.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ------------------------------
# CRUD de Stocks
# ------------------------------
class StockListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={200: StockSerializer(many=True)}
    )
    def get(self, request):
        stocks = Stock.objects.all()
        serializer = StockSerializer(stocks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        request_body=StockSerializer,
        responses={201: StockSerializer, 400: "Error de validación"}
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
        responses={200: StockSerializer, 404: "Stock no encontrado"}
    )
    def get(self, request, pk):
        stock = get_object_or_404(Stock, pk=pk)
        serializer = StockSerializer(stock)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        request_body=StockSerializer,
        responses={200: StockSerializer, 400: "Error de validación", 404: "Stock no encontrado"}
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
        responses={204: 'No Content', 404: "Stock no encontrado"}
    )
    def delete(self, request, pk):
        stock = get_object_or_404(Stock, pk=pk)
        stock.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
