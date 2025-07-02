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
from django.db.models import Q
from datetime import timedelta, datetime
import pytz
from .models import Transaccion, Producto, Stock, Item
from drf_yasg import openapi
import base64
import gzip
import json

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
        # Solo mostrar productos no eliminados, ordenados por fecha de actualización (más recientes primero)
        productos = Producto.objects.filter(eliminado=False).order_by('-actualizado_en', '-creado_en')
        
        # Filtrar por código si se proporciona como parámetro
        codigo_param = request.query_params.get('codigo')
        if codigo_param:
            productos = productos.filter(
                Q(codigo__icontains=codigo_param) | 
                Q(nombre__icontains=codigo_param)
            )
        
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
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
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
    
    

class ProductoBulkImportAPIView(APIView):
    """
    Vista para importación bulk de productos desde CSV.
    Solo agrega productos nuevos (no actualiza existentes).
    Soporta datos comprimidos para archivos grandes.
    """
    permission_classes = [IsAuthenticated]

    def _descomprimir_datos(self, compressed_data):
        """Descomprime datos base64 + gzip (con fallbacks)"""
        try:
            # Intentar decodificar base64 + gzip
            try:
                compressed_bytes = base64.b64decode(compressed_data)
                decompressed_bytes = gzip.decompress(compressed_bytes)
                json_string = decompressed_bytes.decode('utf-8')
                return json.loads(json_string)
            except:
                # Fallback 1: solo base64 estándar
                try:
                    decoded_bytes = base64.b64decode(compressed_data)
                    json_string = decoded_bytes.decode('utf-8')
                    return json.loads(json_string)
                except:
                    # Fallback 2: base64 con URL encoding (compatible con unescape/encodeURIComponent)
                    try:
                        decoded_string = base64.b64decode(compressed_data).decode('utf-8')
                        import urllib.parse
                        unescaped = urllib.parse.unquote(decoded_string)
                        return json.loads(unescaped)
                    except:
                        # Fallback 3: interpretar como JSON directo
                        return json.loads(compressed_data)
        except Exception as e:
            raise ValueError(f"Error al descomprimir datos: {str(e)}")

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'productos': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'codigo': openapi.Schema(type=openapi.TYPE_STRING),
                            'nombre': openapi.Schema(type=openapi.TYPE_STRING),
                            'precio': openapi.Schema(type=openapi.TYPE_INTEGER),
                        }
                    )
                ),
                'productos_compressed': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Datos de productos comprimidos en base64"
                ),
                'chunk_info': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="Información del chunk actual"
                )
            }
        ),
        responses={201: "Productos importados exitosamente", 400: "Error de validación"}
    )
    def post(self, request):
        # Solo administradores pueden importar productos
        if request.user.role != 'ADMIN':
            return Response({"error": "Solo los administradores pueden importar productos"}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        # Obtener datos (comprimidos o normales)
        productos_data = []
        chunk_info = request.data.get('chunk_info', {})
        
        if 'productos_compressed' in request.data:
            # Datos comprimidos
            try:
                productos_data = self._descomprimir_datos(request.data['productos_compressed'])
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Datos normales
            productos_data = request.data.get('productos', [])
        
        if not productos_data:
            return Response({"error": "No se proporcionaron productos para importar"}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        productos_creados = []
        productos_omitidos = []
        errores = []
        
        # Log del chunk si está disponible
        if chunk_info:
            print(f"Procesando chunk {chunk_info.get('current', '?')}/{chunk_info.get('total', '?')} "
                  f"con {len(productos_data)} productos")
        
        with transaction.atomic():
            for producto_data in productos_data:
                codigo = producto_data.get('codigo', '').strip()
                nombre = producto_data.get('nombre', '').strip()
                precio_raw = producto_data.get('precio', '')
                
                # Validar datos básicos
                if not codigo:
                    errores.append(f"Producto sin código: {nombre}")
                    continue
                
                # Procesar precio (manejar valores "null", vacíos o inválidos)
                if precio_raw in [None, '', 'null', 'NULL']:
                    precio = 0
                else:
                    try:
                        precio = int(precio_raw)
                    except (ValueError, TypeError):
                        precio = 0
                
                # Verificar si el producto ya existe
                if Producto.objects.filter(codigo=codigo, eliminado=False).exists():
                    productos_omitidos.append({
                        'codigo': codigo,
                        'nombre': nombre,
                        'razon': 'Ya existe'
                    })
                    continue
                
                # Crear producto
                try:
                    producto = Producto.objects.create(
                        codigo=codigo,
                        nombre=nombre,
                        precio=precio
                    )
                    productos_creados.append({
                        'id': producto.id,
                        'codigo': producto.codigo,
                        'nombre': producto.nombre,
                        'precio': producto.precio
                    })
                except Exception as e:
                    errores.append(f"Error al crear producto {codigo}: {str(e)}")
        
        # Respuesta optimizada para chunks
        chunk_msg = ""
        if chunk_info:
            chunk_msg = f" (Chunk {chunk_info.get('current')}/{chunk_info.get('total')})"
        
        return Response({
            'mensaje': f'Importación completada{chunk_msg}. {len(productos_creados)} productos creados.',
            'productos_creados': len(productos_creados),
            'productos_omitidos': len(productos_omitidos),
            'errores': len(errores),
            'chunk_info': chunk_info,
            'detalle': {
                'creados': productos_creados[:10],  # Solo primeros 10 para evitar respuestas enormes
                'omitidos': productos_omitidos[:10],
                'errores': errores[:10]
            }
        }, status=status.HTTP_201_CREATED)


class ProductoBulkUpdateAPIView(APIView):
    """
    Vista para actualización bulk de productos desde CSV.
    Actualiza productos existentes y crea los que no existen.
    Soporta datos comprimidos para archivos grandes.
    """
    permission_classes = [IsAuthenticated]

    def _descomprimir_datos(self, compressed_data):
        """Descomprime datos base64 + gzip (con fallbacks)"""
        try:
            # Intentar decodificar base64 + gzip
            try:
                compressed_bytes = base64.b64decode(compressed_data)
                decompressed_bytes = gzip.decompress(compressed_bytes)
                json_string = decompressed_bytes.decode('utf-8')
                return json.loads(json_string)
            except:
                # Fallback 1: solo base64 estándar
                try:
                    decoded_bytes = base64.b64decode(compressed_data)
                    json_string = decoded_bytes.decode('utf-8')
                    return json.loads(json_string)
                except:
                    # Fallback 2: base64 con URL encoding (compatible con unescape/encodeURIComponent)
                    try:
                        decoded_string = base64.b64decode(compressed_data).decode('utf-8')
                        import urllib.parse
                        unescaped = urllib.parse.unquote(decoded_string)
                        return json.loads(unescaped)
                    except:
                        # Fallback 3: interpretar como JSON directo
                        return json.loads(compressed_data)
        except Exception as e:
            raise ValueError(f"Error al descomprimir datos: {str(e)}")

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'productos': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'codigo': openapi.Schema(type=openapi.TYPE_STRING),
                            'nombre': openapi.Schema(type=openapi.TYPE_STRING),
                            'precio': openapi.Schema(type=openapi.TYPE_INTEGER),
                        }
                    )
                ),
                'productos_compressed': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Datos de productos comprimidos en base64"
                ),
                'chunk_info': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="Información del chunk actual"
                )
            }
        ),
        responses={200: "Productos actualizados exitosamente", 400: "Error de validación"}
    )
    def post(self, request):
        # Solo administradores pueden actualizar productos
        if request.user.role != 'ADMIN':
            return Response({"error": "Solo los administradores pueden actualizar productos"}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        # Obtener datos (comprimidos o normales)
        productos_data = []
        chunk_info = request.data.get('chunk_info', {})
        
        if 'productos_compressed' in request.data:
            # Datos comprimidos
            try:
                productos_data = self._descomprimir_datos(request.data['productos_compressed'])
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Datos normales
            productos_data = request.data.get('productos', [])
        
        if not productos_data:
            return Response({"error": "No se proporcionaron productos para actualizar"}, 
                          status=status.HTTP_400_BAD_REQUEST)        
        productos_creados = []
        productos_actualizados = []
        errores = []
        
        # Log del chunk si está disponible
        if chunk_info:
            print(f"Procesando chunk {chunk_info.get('current', '?')}/{chunk_info.get('total', '?')} "
                  f"con {len(productos_data)} productos")
        
        with transaction.atomic():
            for producto_data in productos_data:
                codigo = producto_data.get('codigo', '').strip()
                nombre = producto_data.get('nombre', '').strip()
                precio_raw = producto_data.get('precio', '')
                
                # Validar datos básicos
                if not codigo:
                    errores.append(f"Producto sin código: {nombre}")
                    continue
                
                # Procesar precio (manejar valores "null", vacíos o inválidos)
                if precio_raw in [None, '', 'null', 'NULL']:
                    precio = 0
                else:
                    try:
                        precio = int(precio_raw)
                    except (ValueError, TypeError):
                        precio = 0
                
                try:
                    # Buscar producto existente (incluyendo eliminados para poder restaurarlos)
                    producto = Producto.objects.filter(codigo=codigo).first()
                    
                    if producto:
                        # Actualizar producto existente
                        restaurado = producto.eliminado
                        producto.nombre = nombre
                        producto.precio = precio
                        # Si estaba eliminado, restaurarlo
                        if producto.eliminado:
                            producto.eliminado = False
                            producto.eliminado_en = None
                        producto.save()
                        
                        productos_actualizados.append({
                            'id': producto.id,
                            'codigo': producto.codigo,
                            'nombre': producto.nombre,
                            'precio': producto.precio,
                            'accion': 'restaurado' if restaurado else 'actualizado'
                        })
                    else:
                        # Crear producto nuevo
                        producto = Producto.objects.create(
                            codigo=codigo,
                            nombre=nombre,
                            precio=precio
                        )
                        productos_creados.append({
                            'id': producto.id,
                            'codigo': producto.codigo,
                            'nombre': producto.nombre,
                            'precio': producto.precio
                        })
                        
                except Exception as e:
                    errores.append(f"Error al procesar producto {codigo}: {str(e)}")
        
        # Respuesta optimizada para chunks
        chunk_msg = ""
        if chunk_info:
            chunk_msg = f" (Chunk {chunk_info.get('current')}/{chunk_info.get('total')})"
        
        return Response({
            'mensaje': f'Actualización completada{chunk_msg}. {len(productos_creados)} productos creados, {len(productos_actualizados)} actualizados.',
            'productos_creados': len(productos_creados),
            'productos_actualizados': len(productos_actualizados),
            'errores': len(errores),
            'chunk_info': chunk_info,
            'detalle': {
                'creados': productos_creados[:10],  # Solo primeros 10 para evitar respuestas enormes
                'actualizados': productos_actualizados[:10],
                'errores': errores[:10]
            }
        }, status=status.HTTP_200_OK)

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

class TransaccionDetalleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={200: "Detalle de transacción", 404: "Transacción no encontrada"}
    )
    def get(self, request, transaccion_id):
        """Obtener detalles completos de una transacción específica"""
        try:
            transaccion = Transaccion.objects.get(id=transaccion_id, estado='CONFIRMADA')
        except Transaccion.DoesNotExist:
            return Response(
                {"error": "Transacción no encontrada"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Obtener información del vendedor
        vendedor_info = {
            'id': transaccion.usuario.id,
            'username': transaccion.usuario.username,
            'nombre_completo': f"{transaccion.usuario.first_name} {transaccion.usuario.last_name}".strip(),
            'role': transaccion.usuario.role
        }
        
        # Obtener todos los items de la transacción
        items = []
        for item in transaccion.item_set.all():
            items.append({
                'id': item.id,
                'producto_codigo': item.producto.codigo if item.producto else item.producto_codigo,
                'producto_nombre': item.producto.nombre if item.producto else item.producto_nombre,
                'cantidad': item.cantidad,
                'precio_unitario': float(item.producto.precio) if item.producto else float(item.producto_precio or 0),
                'subtotal': float(item.subtotal),
                'producto_activo': item.producto is not None  # Para saber si el producto aún existe
            })
        
        # Calcular totales y descuentos
        total_sin_descuento = float(transaccion.total)
        descuento_aplicado = float(transaccion.descuento_carrito)
        porcentaje_descuento = float(transaccion.porcentaje_descuento)
        total_final = float(transaccion.total_final)
        
        # Convertir fechas a zona horaria local
        chile_tz = pytz.timezone('America/Santiago')
        fecha_creacion = transaccion.creado_en.astimezone(chile_tz) if transaccion.creado_en else None
        fecha_confirmacion = transaccion.confirmado_en.astimezone(chile_tz) if transaccion.confirmado_en else None
        
        detalle = {
            'id': transaccion.id,
            'estado': transaccion.estado,
            'fecha_creacion': fecha_creacion.isoformat() if fecha_creacion else None,
            'fecha_confirmacion': fecha_confirmacion.isoformat() if fecha_confirmacion else None,
            'fecha_creacion_local': fecha_creacion.strftime('%d/%m/%Y %H:%M:%S') if fecha_creacion else None,
            'fecha_confirmacion_local': fecha_confirmacion.strftime('%d/%m/%Y %H:%M:%S') if fecha_confirmacion else None,
            'vendedor': vendedor_info,
            'items': items,
            'total_sin_descuento': total_sin_descuento,
            'descuento_aplicado': descuento_aplicado,
            'porcentaje_descuento': porcentaje_descuento,
            'total_final': total_final,
            'cantidad_items': len(items),
            'cantidad_productos': sum(item['cantidad'] for item in items)
        }
        
        return Response(detalle, status=status.HTTP_200_OK)

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
        # Obtener timezone de Chile
        chile_tz = pytz.timezone('America/Santiago')
        now_chile = timezone.now().astimezone(chile_tz)
        hoy_chile = now_chile.date()
        
        # Calcular inicio y fin del día en Chile, convertir a UTC para la consulta
        inicio_dia_chile = chile_tz.localize(datetime.combine(hoy_chile, datetime.min.time()))
        fin_dia_chile = chile_tz.localize(datetime.combine(hoy_chile, datetime.max.time()))
        
        inicio_dia_utc = inicio_dia_chile.astimezone(pytz.UTC)
        fin_dia_utc = fin_dia_chile.astimezone(pytz.UTC)
        
        # Ventas del día en Chile
        transacciones_hoy = Transaccion.objects.filter(
            estado='CONFIRMADA',
            confirmado_en__gte=inicio_dia_utc,
            confirmado_en__lte=fin_dia_utc
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
        # Obtener timezone de Chile
        chile_tz = pytz.timezone('America/Santiago')
        now_chile = timezone.now().astimezone(chile_tz)
        hoy_chile = now_chile.date()
        
        # Calcular inicio y fin del día en Chile, convertir a UTC para la consulta
        inicio_dia_chile = chile_tz.localize(datetime.combine(hoy_chile, datetime.min.time()))
        fin_dia_chile = chile_tz.localize(datetime.combine(hoy_chile, datetime.max.time()))
        
        inicio_dia_utc = inicio_dia_chile.astimezone(pytz.UTC)
        fin_dia_utc = fin_dia_chile.astimezone(pytz.UTC)
        
        # Ventas del día en Chile
        transacciones_hoy = Transaccion.objects.filter(
            estado='CONFIRMADA',
            confirmado_en__gte=inicio_dia_utc,
            confirmado_en__lte=fin_dia_utc
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
        ],        responses={200: "Datos del gráfico de ventas"}
    )
    def get(self, request):
        period = request.query_params.get('period', 'day')
        
        # Obtener timezone de Chile
        chile_tz = pytz.timezone('America/Santiago')
        now_chile = timezone.now().astimezone(chile_tz)
        
        labels = []
        data = []
        
        if period == 'day':
            # Datos por hora para el día actual en Chile
            start_of_day_chile = now_chile.replace(hour=0, minute=0, second=0, microsecond=0)
            
            for hour in range(24):
                hour_start_chile = start_of_day_chile + timedelta(hours=hour)
                hour_end_chile = hour_start_chile + timedelta(hours=1)
                
                # Convertir a UTC para la consulta
                hour_start_utc = hour_start_chile.astimezone(pytz.UTC)
                hour_end_utc = hour_end_chile.astimezone(pytz.UTC)
                
                sales = Transaccion.objects.filter(
                    estado='CONFIRMADA',
                    confirmado_en__gte=hour_start_utc,
                    confirmado_en__lt=hour_end_utc
                )
                total = sum(t.total_final for t in sales)
                data.append(float(total))
                labels.append(f"{hour}:00")
        
        elif period == 'week':
            # Datos por día para la semana actual en Chile
            start_of_week_chile = now_chile - timedelta(days=now_chile.weekday())
            start_of_week_chile = start_of_week_chile.replace(hour=0, minute=0, second=0, microsecond=0)
            
            for day in range(7):
                day_start_chile = start_of_week_chile + timedelta(days=day)
                day_end_chile = day_start_chile + timedelta(days=1)
                
                # Convertir a UTC para la consulta
                day_start_utc = day_start_chile.astimezone(pytz.UTC)
                day_end_utc = day_end_chile.astimezone(pytz.UTC)
                
                sales = Transaccion.objects.filter(
                    estado='CONFIRMADA',
                    confirmado_en__gte=day_start_utc,
                    confirmado_en__lt=day_end_utc
                )
                total = sum(t.total_final for t in sales)
                data.append(float(total))
                labels.append(day_start_chile.strftime('%a'))
        
        elif period == 'month':
            # Datos por semana para el mes actual en Chile
            start_of_month_chile = now_chile.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if start_of_month_chile.month == 12:
                next_month_chile = start_of_month_chile.replace(year=start_of_month_chile.year+1, month=1)
            else:
                next_month_chile = start_of_month_chile.replace(month=start_of_month_chile.month+1)
            
            current_week = start_of_month_chile
            week_number = 1
            while current_week < next_month_chile:
                week_end = current_week + timedelta(weeks=1)
                if week_end > next_month_chile:
                    week_end = next_month_chile
                
                # Convertir a UTC para la consulta
                week_start_utc = current_week.astimezone(pytz.UTC)
                week_end_utc = week_end.astimezone(pytz.UTC)
                
                sales = Transaccion.objects.filter(
                    estado='CONFIRMADA',
                    confirmado_en__gte=week_start_utc,
                    confirmado_en__lt=week_end_utc
                )
                total = sum(t.total_final for t in sales)
                data.append(float(total))
                labels.append(f"Semana {week_number}")
                current_week = week_end
                week_number += 1
        
        elif period == 'year':
            # Datos por mes para el año actual en Chile
            start_of_year_chile = now_chile.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            
            for month in range(12):
                month_start = start_of_year_chile.replace(month=month+1)
                if month == 11:  # Diciembre
                    month_end = month_start.replace(year=month_start.year+1, month=1)
                else:
                    month_end = month_start.replace(month=month+2)
                  # Convertir a UTC para la consulta
                month_start_utc = month_start.astimezone(pytz.UTC)
                month_end_utc = month_end.astimezone(pytz.UTC)
                
                sales = Transaccion.objects.filter(
                    estado='CONFIRMADA',
                    confirmado_en__gte=month_start_utc,
                    confirmado_en__lt=month_end_utc
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
            openapi.Parameter('producto', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Filtrar por producto (código o nombre)'),
        ]
    )
    def get(self, request):
        """Obtener historial de ventas con filtros opcionales"""
        transacciones = Transaccion.objects.filter(estado='CONFIRMADA').order_by('-confirmado_en')
        
        # Aplicar filtros si existen
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        vendedor = request.query_params.get('vendedor')
        producto = request.query_params.get('producto')
        
        if fecha_inicio:
            transacciones = transacciones.filter(confirmado_en__date__gte=fecha_inicio)
        if fecha_fin:
            transacciones = transacciones.filter(confirmado_en__date__lte=fecha_fin)
        if vendedor:
            transacciones = transacciones.filter(usuario__username__icontains=vendedor)
        if producto:
            # Filtrar por transacciones que contengan productos con el código o nombre especificado
            from django.db.models import Q
            transacciones = transacciones.filter(
                Q(item__producto__codigo__icontains=producto) |
                Q(item__producto__nombre__icontains=producto) |
                Q(item__producto_nombre__icontains=producto)
            ).distinct()
          # Serializar datos
        historial = []
        for transaccion in transacciones:
            # Convertir fecha a zona horaria local
            chile_tz = pytz.timezone('America/Santiago')
            fecha_local = transaccion.confirmado_en.astimezone(chile_tz) if transaccion.confirmado_en else None
            
            historial.append({
                'id': transaccion.id,
                'creado_en': transaccion.creado_en.isoformat() if transaccion.creado_en else None,
                'fecha': fecha_local.isoformat() if fecha_local else None,
                'fecha_local': fecha_local.strftime('%d/%m/%Y %H:%M:%S') if fecha_local else None,
                'vendedor': f"{transaccion.usuario.first_name} {transaccion.usuario.last_name}".strip() or transaccion.usuario.username,
                'vendedor_username': transaccion.usuario.username,
                'total': float(transaccion.total_final),'items': [
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
