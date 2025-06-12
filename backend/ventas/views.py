# /backend/ventas/views.py

from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

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
    UserCreateSerializer,
    UserUpdateSerializer,
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

    def post(self, request, pk):
        try:
            transaccion = Transaccion.objects.get(pk=pk, estado='PENDIENTE')
        except Transaccion.DoesNotExist:
            return Response(
                {'error': 'Transacción no encontrada o ya procesada'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verificar stock para cada ítem
        items_sin_stock = []
        for item in transaccion.item_set.all():
            try:
                stock = Stock.objects.get(producto=item.producto)
                if stock.cantidad < item.cantidad:
                    items_sin_stock.append({
                        'producto': item.producto.nombre,
                        'codigo': item.producto.codigo,
                        'stock_disponible': stock.cantidad,
                        'cantidad_solicitada': item.cantidad
                    })
            except Stock.DoesNotExist:
                items_sin_stock.append({
                    'producto': item.producto.nombre,
                    'codigo': item.producto.codigo,
                    'stock_disponible': 0,
                    'cantidad_solicitada': item.cantidad
                })

        # Verificar permisos según rol del usuario
        usuario = request.user
        
        if items_sin_stock:
            if usuario.role == 'EMPLOYEE':
                # EMPLEADOS: No pueden vender con stock insuficiente
                productos_problemáticos = [item['producto'] for item in items_sin_stock]
                return Response({
                    'error': 'Venta no autorizada',
                    'detalle': f'No puedes realizar ventas con stock insuficiente para: {", ".join(productos_problemáticos)}',
                    'items_sin_stock': items_sin_stock,
                    'usuario_role': usuario.role,
                    'tipo_error': 'STOCK_INSUFICIENTE_EMPLEADO'
                }, status=status.HTTP_403_FORBIDDEN)
            elif usuario.role == 'ADMIN':
                # ADMIN: Puede vender pero se registra la situación
                productos_con_problema = [f"{item['producto']} (stock: {item['stock_disponible']}, solicitado: {item['cantidad_solicitada']})" for item in items_sin_stock]
                print(f"[ADVERTENCIA] Admin {usuario.username} realizó venta con stock insuficiente en productos: {', '.join(productos_con_problema)}")
                # Continúa con la venta
        
        # Procesar la venta (actualizar stock y confirmar transacción)
        for item in transaccion.item_set.all():
            try:
                stock = Stock.objects.get(producto=item.producto)
                stock.cantidad -= item.cantidad
                stock.save()
            except Stock.DoesNotExist:
                # Si no existe stock, crear uno con cantidad negativa (solo para admins)
                Stock.objects.create(producto=item.producto, cantidad=-item.cantidad)

        # Confirmar transacción
        transaccion.estado = 'CONFIRMADA'
        transaccion.confirmado_en = timezone.now()
        transaccion.save()

        return Response({
            'mensaje': 'Transacción confirmada exitosamente',
            'transaccion_id': transaccion.id,
            'total_final': float(transaccion.total_final),
            'items_sin_stock': items_sin_stock if usuario.role == 'ADMIN' and items_sin_stock else None
        }, status=status.HTTP_200_OK)


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
        responses={204: 'No Content', 404: "Producto no encontrado", 400: "Producto en uso"}
    )
    def delete(self, request, pk):
        from django.db.models.deletion import ProtectedError
        
        producto = get_object_or_404(Producto, pk=pk)
        try:
            producto.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError as e:
            # El producto está siendo usado en transacciones
            return Response({
                'error': 'No se puede eliminar el producto',
                'detalle': 'Este producto está siendo utilizado en transacciones existentes. No se puede eliminar para preservar el historial de ventas.',
                'codigo_producto': producto.codigo,
                'nombre_producto': producto.nombre,
                'sugerencia': 'Considera desactivar el producto en lugar de eliminarlo si ya no quieres que esté disponible para venta.'
            }, status=status.HTTP_400_BAD_REQUEST)


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
        # Permitir filtrar por producto si se proporciona el parámetro
        producto_id = request.query_params.get('producto')
        if producto_id:
            stocks = Stock.objects.filter(producto_id=producto_id)
        else:
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
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={204: 'No Content', 404: "Stock no encontrado"}
    )
    def delete(self, request, pk):
        stock = get_object_or_404(Stock, pk=pk)
        stock.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ------------------------------
# Gestión de Usuarios (solo para administradores)
# ------------------------------
from django.contrib.auth import get_user_model
from rest_framework.permissions import BasePermission

User = get_user_model()

class IsAdminUser(BasePermission):
    """
    Permiso personalizado para permitir solo a usuarios con rol ADMIN
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'ADMIN'


class UserListCreateAPIView(APIView):
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={200: UserSerializer(many=True)}
    )
    def get(self, request):
        """Listar todos los usuarios (solo administradores)"""
        users = User.objects.all().order_by('-date_joined')
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        request_body=UserCreateSerializer,
        responses={201: UserSerializer, 400: "Error de validación"}
    )
    def post(self, request):
        """Crear un nuevo usuario (solo administradores)"""
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailAPIView(APIView):
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={200: UserSerializer, 404: "Usuario no encontrado"}
    )
    def get(self, request, pk):
        """Obtener detalle de un usuario"""
        user = get_object_or_404(User, pk=pk)
        serializer = UserSerializer(user)
        return Response(serializer.data)

    @swagger_auto_schema(
        request_body=UserUpdateSerializer,
        responses={200: UserSerializer, 400: "Error de validación", 404: "Usuario no encontrado"}
    )
    def put(self, request, pk):
        """Actualizar un usuario"""
        user = get_object_or_404(User, pk=pk)
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserSerializer(user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={204: 'No Content', 404: "Usuario no encontrado"}
    )
    def delete(self, request, pk):
        """Eliminar un usuario"""
        user = get_object_or_404(User, pk=pk)
        if user == request.user:
            return Response(
                {"error": "No puedes eliminar tu propia cuenta"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserProfileAPIView(APIView):
    """
    Vista para que cualquier usuario autenticado pueda ver su propio perfil
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={200: UserSerializer}
    )
    def get(self, request):
        """Obtener perfil del usuario actual"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class UsuarioActualAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Devuelve información del usuario autenticado"""
        user = request.user
        return Response({
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'role_display': user.get_role_display()
        })


# ------------------------------
# Consultas y reportes
# ------------------------------
class ReporteStockBajoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={200: StockSerializer(many=True)}
    )
    def get(self, request):
        """
        Reporte de productos con stock bajo (menos de 10 unidades)
        """
        umbral_bajo = 10
        stocks_bajos = Stock.objects.filter(cantidad__lt=umbral_bajo)
        serializer = StockSerializer(stocks_bajos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ReporteVentasDiariasAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={200: 'Lista de transacciones diarias'}
    )
    def get(self, request):
        """
        Reporte de ventas diarias (todas las transacciones del día actual)
        """
        hoy = timezone.now().date()
        transacciones_hoy = Transaccion.objects.filter(confirmado_en__date=hoy)
        
        # Detalle de cada transacción
        resultados = []
        for transaccion in transacciones_hoy:
            detalle = TransaccionDetailSerializer(transaccion)
            resultados.append(detalle.data)
        
        return Response(resultados, status=status.HTTP_200_OK)
