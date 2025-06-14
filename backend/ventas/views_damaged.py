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
from .models import Transaccion
from drf_yasg import openapi

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
    HistorialVentasSerializer, 
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

        # 1) Crear la Transaccion en estado PENDIENTE y asignar el vendedor
        transaccion = Transaccion.objects.create(
            usuario=request.user,
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

# -----------------------
#  Metricas de venta 
# ----------------------

class MetricsView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retorna la suma total de ventas confirmadas del día, semana y mes actual.",
        responses={
            200: openapi.Response(
                description="Totales de ventas por período",
                examples={
                    "application/json": {
                        "hoy": {"ventas": 30000.0, "cantidad_transacciones": 5},
                        "semana": {"ventas": 150000.0, "cantidad_transacciones": 22},
                        "mes": {"ventas": 340000.0, "cantidad_transacciones": 48}
                    }
                }
            )
        }
    )
    def get(self, request):
        now = timezone.now()

        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_week = start_of_day - timedelta(days=now.weekday())  # Lunes
        start_of_month = start_of_day.replace(day=1)

        def get_metrics_for_period(start_date): # Renamed to avoid conflict and clarify scope
            transacciones = Transaccion.objects.filter(
                estado='CONFIRMADA',
                confirmado_en__gte=start_date
            )

            total_ventas = sum(t.total_final for t in transacciones)
            cantidad = transacciones.count()

            return {
                'dinero_total': float(round(total_ventas, 2)),
                'cantidad_de_transacciones': cantidad
            }

        return Response({ # Moved return Response to the main get method
            'hoy': get_metrics_for_period(start_of_day),
            'semana': get_metrics_for_period(start_of_week),
            'mes': get_metrics_for_period(start_of_month),
        })

# -----------------------
#  Métricas de dashboard
# ----------------------
    
class DashboardMetricsView(APIView): # Un-nested
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retorna métricas clave para el dashboard: ventas de hoy, total de productos y usuario actual.",
        responses={
            200: openapi.Response(
                description="Métricas del dashboard",
                examples={
                    "application/json": {
                        "ventas_hoy": {"monto": 55000.0, "cantidad": 3},
                        "total_productos": 150,
                        "usuario_actual": "admin_user"
                    }
                }
            )
        }
    )
    def get(self, request):
        now = timezone.now()
        
        # Ventas hoy
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        ventas_hoy_qs = Transaccion.objects.filter(
            estado='CONFIRMADA',
            confirmado_en__gte=start_of_day
        )
        total_ventas_hoy = sum(t.total_final for t in ventas_hoy_qs)
        cantidad_ventas_hoy = ventas_hoy_qs.count()

        # Total productos
        total_productos = Producto.objects.count()

        return Response({
            'ventas_hoy': {
                'monto': float(round(total_ventas_hoy, 2)),
                'cantidad': cantidad_ventas_hoy
            },
            'total_productos': total_productos,
            'usuario_actual': request.user.username
        })

class SalesChartDataView(APIView): # Un-nested
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retorna datos para el gráfico de ventas, filtrados por período (day, week, month, year).",
        manual_parameters=[
            openapi.Parameter('period', openapi.IN_QUERY, description="Período para los datos del gráfico (day, week, month, year)", type=openapi.TYPE_STRING, default='day')
        ],
        responses={
            200: openapi.Response(
                description="Datos para el gráfico",
                examples={
                    "application/json": {
                        "labels": ["00:00", "01:00", "..."],
                        "data": [150.0, 200.0, "..."]
                    }
                }
            )
        }
    )
    def get(self, request):
        period = request.query_params.get('period', 'day')
        now = timezone.now()
        data = []
        labels = []

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
        # Aquí se puede implementar la lógica del historial de ventas
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
                'total': float(transaccion.total_final),
                'items': [
                    {
                        'producto': item.producto.nombre,
                        'cantidad': item.cantidad,
                        'precio_unitario': float(item.precio_unitario),
                        'subtotal': float(item.subtotal)
                    }
                    for item in transaccion.items.all()
                ]
            })
        
        return Response(historial, status=status.HTTP_200_OK)

# ------------------------------
# Gestión de Usuarios (solo para administradores)
# ------------------------------

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
        responses={200: HistorialVentasSerializer(many=True)}
    )
    def get(self, request):
        """
        Devuelve todas las transacciones con vendedor, total_final, fecha y detalle de items.
        """
        qs = Transaccion.objects.select_related('usuario')\
                                .prefetch_related('item_set__producto')\
                                .all()
        serializer = HistorialVentasSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
