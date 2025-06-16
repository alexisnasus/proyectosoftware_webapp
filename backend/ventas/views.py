# /backend/ventas/views.py

from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework import status
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
from .models import Transaccion, Producto, Stock, Item
from drf_yasg import openapi

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    InputItemDTO,
    InputTransaccionSerializer,
    TransaccionDetailSerializer,
    MyTokenObtainPairSerializer,
    ProductoSerializer,
    StockSerializer,
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    HistorialVentasSerializer,
)

User = get_user_model()

# ------------------------------
# Permisos personalizados
# ------------------------------

class IsAdminUser(BasePermission):
    """
    Permiso personalizado para permitir solo a usuarios con rol ADMIN
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'ADMIN'

# ------------------------------
# Autenticación y gestión de usuarios
# ------------------------------

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={200: "Logout exitoso"}
    )
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({"mensaje": "Logout exitoso"}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Token inválido"}, status=status.HTTP_400_BAD_REQUEST)

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={200: UserSerializer}
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

# ------------------------------
# Gestión de Usuarios (solo para administradores)
# ------------------------------

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
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        request_body=UserCreateSerializer,
        responses={201: UserSerializer, 400: "Error de validación"}
    )
    def post(self, request):
        """Crear nuevo usuario (solo administradores)"""
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            response_serializer = UserSerializer(user)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserDetailAPIView(APIView):
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={200: UserSerializer, 404: "Usuario no encontrado"}
    )
    def get(self, request, pk):
        """Obtener detalles de un usuario específico"""
        user = get_object_or_404(User, pk=pk)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        request_body=UserUpdateSerializer,
        responses={200: UserSerializer, 400: "Error de validación", 404: "Usuario no encontrado"}
    )
    def put(self, request, pk):
        """Actualizar usuario (solo administradores)"""
        user = get_object_or_404(User, pk=pk)
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            user = serializer.save()
            response_serializer = UserSerializer(user)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={204: "Usuario eliminado", 404: "Usuario no encontrado"}
    )
    def delete(self, request, pk):
        """Eliminar usuario (solo administradores)"""
        user = get_object_or_404(User, pk=pk)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={200: UserSerializer}
    )
    def get(self, request):
        """Obtener perfil del usuario actual"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UsuarioActualAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={200: "Usuario actual"}
    )
    def get(self, request):
        """Obtener información básica del usuario actual"""
        return Response({
            'id': request.user.id,
            'username': request.user.username,
            'role': request.user.role,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
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
        # Solo mostrar productos no eliminados
        productos = Producto.objects.filter(eliminado=False)
        serializer = ProductoSerializer(productos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        request_body=ProductoSerializer,
        responses={201: ProductoSerializer, 400: "Error de validación"}
    )
    def post(self, request):
        # Solo administradores pueden crear productos
        if request.user.role != 'ADMIN':
            return Response({"error": "Solo los administradores pueden crear productos"}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        serializer = ProductoSerializer(data=request.data)
        if serializer.is_valid():
            producto = serializer.save()
            return Response(ProductoSerializer(producto).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProductoDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={200: ProductoSerializer, 404: "Producto no encontrado"}
    )
    def get(self, request, pk):
        producto = get_object_or_404(Producto, pk=pk, eliminado=False)
        serializer = ProductoSerializer(producto)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        request_body=ProductoSerializer,
        responses={200: ProductoSerializer, 400: "Error de validación", 404: "Producto no encontrado"}
    )
    def put(self, request, pk):
        # Solo administradores pueden editar productos
        if request.user.role != 'ADMIN':
            return Response({"error": "Solo los administradores pueden editar productos"}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        producto = get_object_or_404(Producto, pk=pk, eliminado=False)
        serializer = ProductoSerializer(producto, data=request.data, partial=True)
        if serializer.is_valid():
            producto = serializer.save()
            return Response(ProductoSerializer(producto).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={204: "Producto eliminado", 404: "Producto no encontrado"}
    )
    def delete(self, request, pk):
        # Solo administradores pueden eliminar productos
        if request.user.role != 'ADMIN':
            return Response({"error": "Solo los administradores pueden eliminar productos"}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        producto = get_object_or_404(Producto, pk=pk, eliminado=False)
        # Soft delete: marcar como eliminado en lugar de borrar físicamente
        producto.eliminado = True
        producto.eliminado_en = timezone.now()
        producto.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

# ------------------------------
# CRUD de Stock
# ------------------------------

class StockListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={200: StockSerializer(many=True)}
    )
    def get(self, request):
        stocks = Stock.objects.all()
        
        # Filtrar por producto si se proporciona el parámetro
        producto_id = request.query_params.get('producto')
        if producto_id:
            stocks = stocks.filter(producto_id=producto_id)
        
        serializer = StockSerializer(stocks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        request_body=StockSerializer,
        responses={201: StockSerializer, 400: "Error de validación"}
    )
    def post(self, request):
        # Solo administradores pueden crear/modificar stock
        if request.user.role != 'ADMIN':
            return Response({"error": "Solo los administradores pueden crear stock"}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        serializer = StockSerializer(data=request.data)
        if serializer.is_valid():
            stock = serializer.save()
            return Response(StockSerializer(stock).data, status=status.HTTP_201_CREATED)
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
        # Solo administradores pueden editar stock
        if request.user.role != 'ADMIN':
            return Response({"error": "Solo los administradores pueden editar stock"}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        stock = get_object_or_404(Stock, pk=pk)
        serializer = StockSerializer(stock, data=request.data, partial=True)
        if serializer.is_valid():
            stock = serializer.save()
            return Response(StockSerializer(stock).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={204: "Stock eliminado", 404: "Stock no encontrado"}
    )
    def delete(self, request, pk):
        # Solo administradores pueden eliminar stock
        if request.user.role != 'ADMIN':
            return Response({"error": "Solo los administradores pueden eliminar stock"}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        stock = get_object_or_404(Stock, pk=pk)
        stock.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# ------------------------------
# Gestión de Transacciones
# ------------------------------

class TransaccionCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        request_body=InputTransaccionSerializer,
        responses={201: TransaccionDetailSerializer, 400: "Error de validación"}
    )
    def post(self, request):
        serializer = InputTransaccionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        items_data = data['items']
        porcentaje_descuento = data.get('porcentaje_descuento', 0)        # Validar que todos los productos existan y no estén eliminados (usar codigo en lugar de producto_id)
        productos_codigos = [item['codigo'] for item in items_data]
        productos = {p.codigo: p for p in Producto.objects.filter(codigo__in=productos_codigos, eliminado=False)}
        
        if len(productos) != len(productos_codigos):
            codigos_no_encontrados = set(productos_codigos) - set(productos.keys())
            return Response({
                "error": "Algunos productos no existen", 
                "codigos_no_encontrados": list(codigos_no_encontrados)
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validar stock solo para empleados (los admins pueden vender sin stock)
        items_sin_stock = []
        if request.user.role == 'EMPLOYEE':
            for item_data in items_data:
                producto = productos[item_data['codigo']]
                try:
                    stock = Stock.objects.get(producto=producto)
                    if stock.cantidad < item_data['cantidad']:
                        items_sin_stock.append({
                            'producto': producto.nombre,
                            'stock_disponible': stock.cantidad,
                            'cantidad_solicitada': item_data['cantidad']
                        })
                except Stock.DoesNotExist:
                    items_sin_stock.append({
                        'producto': producto.nombre,
                        'stock_disponible': 0,
                        'cantidad_solicitada': item_data['cantidad']
                    })
            
            if items_sin_stock:
                return Response({
                    "error": "Stock insuficiente",
                    "tipo_error": "STOCK_INSUFICIENTE_EMPLEADO",
                    "items_sin_stock": items_sin_stock
                }, status=status.HTTP_403_FORBIDDEN)        # Crear transacción
        try:
            with transaction.atomic():
                # Calcular descuento en valor absoluto primero
                subtotal_temp = 0
                for item_data in items_data:
                    producto = productos[item_data['codigo']]
                    cantidad = item_data['cantidad']
                    item_subtotal = producto.precio * cantidad
                    subtotal_temp += item_subtotal
                
                descuento_valor = (subtotal_temp * porcentaje_descuento) / 100
                
                # Crear la transacción con el descuento calculado
                transaccion = Transaccion.objects.create(
                    usuario=request.user,
                    porcentaje_descuento=porcentaje_descuento,
                    descuento_carrito=descuento_valor,
                    estado='PENDIENTE'
                )

                # Crear los items
                for item_data in items_data:
                    producto = productos[item_data['codigo']]
                    cantidad = item_data['cantidad']

                    # Crear el Item con información histórica del producto
                    Item.objects.create(
                        transaccion=transaccion,
                        producto=producto,
                        producto_codigo=producto.codigo,
                        producto_nombre=producto.nombre,
                        producto_precio=producto.precio,
                        cantidad=cantidad
                    )

                serializer = TransaccionDetailSerializer(transaccion)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TransaccionDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={200: TransaccionDetailSerializer, 404: "Transacción no encontrada"}
    )
    def get(self, request, pk):
        transaccion = get_object_or_404(Transaccion, pk=pk)
        serializer = TransaccionDetailSerializer(transaccion)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ConfirmarTransaccionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={200: "Transacción confirmada", 404: "Transacción no encontrada", 400: "Error de validación"}
    )
    def post(self, request, pk):
        transaccion = get_object_or_404(Transaccion, pk=pk)
        
        if transaccion.estado == 'CONFIRMADA':
            return Response({"error": "La transacción ya está confirmada"}, status=status.HTTP_400_BAD_REQUEST)

        usuario = request.user
        items_sin_stock = []        # Actualizar stock
        for item in transaccion.item_set.all():
            try:
                stock = Stock.objects.get(producto=item.producto)
                # Verificar stock solo para empleados
                if usuario.role == 'EMPLOYEE' and stock.cantidad < item.cantidad:
                    items_sin_stock.append({
                        'producto': item.producto.nombre,
                        'stock_disponible': stock.cantidad,
                        'cantidad_solicitada': item.cantidad
                    })
                    continue
                
                stock.cantidad -= item.cantidad
                stock.save()
            except Stock.DoesNotExist:
                # Si no existe stock, crear uno con cantidad negativa (solo para admins)
                if usuario.role == 'ADMIN':
                    Stock.objects.create(producto=item.producto, cantidad=-item.cantidad)
                else:
                    items_sin_stock.append({
                        'producto': item.producto.nombre,
                        'stock_disponible': 0,
                        'cantidad_solicitada': item.cantidad
                    })

        # Para empleados, no permitir venta si hay items sin stock
        if usuario.role == 'EMPLOYEE' and items_sin_stock:
            return Response({
                "error": "Stock insuficiente",
                "items_sin_stock": items_sin_stock
            }, status=status.HTTP_400_BAD_REQUEST)

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
# Métricas y Dashboard
# ------------------------------

class MetricsView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={200: "Métricas básicas"}
    )
    def get(self, request):
        hoy = timezone.now().date()
          # Ventas del día
        transacciones_hoy = Transaccion.objects.filter(
            estado='CONFIRMADA',
            confirmado_en__date=hoy
        )
        
        cantidad_ventas = transacciones_hoy.count()
        monto_total = sum(t.total_final for t in transacciones_hoy)
        
        # Total productos en inventario (no eliminados)
        total_productos = Producto.objects.filter(eliminado=False).count()
        
        return Response({
            'ventas_hoy': {
                'cantidad': cantidad_ventas,
                'monto': float(monto_total)
            },
            'total_productos': total_productos,
            'usuario_actual': request.user.username
        })

class DashboardMetricsView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={200: "Métricas del dashboard"}
    )
    def get(self, request):
        hoy = timezone.now().date()
        
        # Ventas del día
        transacciones_hoy = Transaccion.objects.filter(
            estado='CONFIRMADA',
            confirmado_en__date=hoy
        )
        
        cantidad_ventas = transacciones_hoy.count()
        monto_total = sum(t.total_final for t in transacciones_hoy)
          # Total productos en inventario (no eliminados)
        total_productos = Producto.objects.filter(eliminado=False).count()
        
        return Response({
            'ventas_hoy': {
                'cantidad': cantidad_ventas,
                'monto': float(monto_total)
            },
            'total_productos': total_productos,
            'usuario_actual': request.user.username
        })

class SalesChartDataView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        manual_parameters=[
            openapi.Parameter('period', openapi.IN_QUERY, type=openapi.TYPE_STRING, 
                            description='Período: day, week, month, year')
        ],
        responses={200: "Datos del gráfico de ventas"}
    )
    def get(self, request):
      
        period = request.query_params.get('period', 'day')
        now = timezone.now()
        labels = []
        data = []
        
        if period == 'day':
            # Datos por hora para el día actual
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            for hour in range(24):
                hour_start = start_of_day + timedelta(hours=hour)
                hour_end = hour_start + timedelta(hours=1)
                sales = Transaccion.objects.filter(
                    estado='CONFIRMADA',
                    confirmado_en__gte=hour_start,
                    confirmado_en__lt=hour_end
                )
                total = sum(t.total_final for t in sales)
                data.append(float(total))
                labels.append(f"{hour}:00")
        
        elif period == 'week':
            # Datos por día para la semana actual
            start_of_week = now - timedelta(days=now.weekday())
            for day in range(7):
                day_start = start_of_week + timedelta(days=day)
                day_end = day_start + timedelta(days=1)
                sales = Transaccion.objects.filter(
                    estado='CONFIRMADA',
                    confirmado_en__gte=day_start,
                    confirmado_en__lt=day_end
                )
                total = sum(t.total_final for t in sales)
                data.append(float(total))
                labels.append(day_start.strftime('%a'))
        
        elif period == 'month':
            # Datos por semana para el mes actual
            start_of_month = now.replace(day=1)
            next_month = start_of_month.replace(month=start_of_month.month+1) if start_of_month.month < 12 else start_of_month.replace(year=start_of_month.year+1, month=1)
            
            current_week = start_of_month
            while current_week < next_month:
                week_end = current_week + timedelta(weeks=1)
                if week_end > next_month:
                    week_end = next_month
                
                sales = Transaccion.objects.filter(
                    estado='CONFIRMADA',
                    confirmado_en__gte=current_week,
                    confirmado_en__lt=week_end
                )
                total = sum(t.total_final for t in sales)
                data.append(float(total))
                labels.append(f"Semana {(current_week.day // 7) + 1}")
                current_week = week_end
        
        elif period == 'year':
            # Datos por mes para el año actual
            start_of_year = now.replace(month=1, day=1)
            for month in range(12):
                month_start = start_of_year.replace(month=month+1)
                month_end = month_start.replace(month=month+2) if month < 11 else month_start.replace(year=month_start.year+1, month=1)
                sales = Transaccion.objects.filter(
                    estado='CONFIRMADA',
                    confirmado_en__gte=month_start,
                    confirmado_en__lt=month_end
                )
                total = sum(t.total_final for t in sales)
                data.append(float(total))
                labels.append(month_start.strftime('%b'))

        return Response({
            'labels': labels,
            'data': data
        })
# ------------------------------
# Historial de Ventas
# ------------------------------

class HistorialVentasAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        manual_parameters=[
            openapi.Parameter('fecha_inicio', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Fecha inicio (YYYY-MM-DD)'),
            openapi.Parameter('fecha_fin', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Fecha fin (YYYY-MM-DD)'),
            openapi.Parameter('vendedor', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Filtrar por vendedor'),
        ]
    )
    def get(self, request):
        """Obtener historial de ventas con filtros opcionales"""
        transacciones = Transaccion.objects.filter(estado='CONFIRMADA').order_by('-confirmado_en')
        
        # Aplicar filtros si existen
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        vendedor = request.query_params.get('vendedor')
        
        if fecha_inicio:
            transacciones = transacciones.filter(confirmado_en__date__gte=fecha_inicio)
        if fecha_fin:
            transacciones = transacciones.filter(confirmado_en__date__lte=fecha_fin)
        if vendedor:
            transacciones = transacciones.filter(usuario__username__icontains=vendedor)
        
        # Serializar datos
        historial = []
        for transaccion in transacciones:
            historial.append({
                'id': transaccion.id,
                'fecha': transaccion.confirmado_en,
                'vendedor': transaccion.usuario.username,
                'total': float(transaccion.total_final),                'items': [
                    {
                        'producto': item.producto.nombre if item.producto else item.producto_nombre,
                        'cantidad': item.cantidad,
                        'precio_unitario': float(item.producto_precio) if item.producto_precio else 0,
                        'subtotal': float(item.subtotal)
                    }
                    for item in transaccion.item_set.all()
                ]
            })
        
        return Response(historial, status=status.HTTP_200_OK)
