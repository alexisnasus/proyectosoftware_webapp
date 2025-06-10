# /backend/ventas/views.py

from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
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
            transaccion.confirmado_en = timezone.now()
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


