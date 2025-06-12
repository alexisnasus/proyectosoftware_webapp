# /backend/ventas/urls.py

from django.urls import path, include
from .views import (
    MyTokenObtainPairView,
    LogoutView,
    MeView,
    # Transacciones:
    TransaccionCreateAPIView,
    TransaccionDetailAPIView,
    ConfirmarTransaccionAPIView,
    # CRUD Productos y Stocks:
    ProductoListCreateAPIView,
    ProductoDetailAPIView,
    StockListCreateAPIView,
    StockDetailAPIView,
    # Gestión de usuarios:
    UserListCreateAPIView,
    UserDetailAPIView,
    UserProfileAPIView,
    UsuarioActualAPIView,
)
from rest_framework_simplejwt.views import TokenRefreshView

auth_urls = [
    path('login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('logout/', LogoutView.as_view(), name='auth_logout'),
    path('me/', MeView.as_view(), name='auth_me'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

urlpatterns = [
    # Rutas de autenticación
    path('user/', include(auth_urls)),

    # --- Gestión de Usuarios (solo para administradores) ---
    path('usuarios/', UserListCreateAPIView.as_view(), name='user-list-create'),
    path('usuarios/<int:pk>/', UserDetailAPIView.as_view(), name='user-detail'),
    path('profile/', UserProfileAPIView.as_view(), name='user-profile'),
    path('usuario-actual/', UsuarioActualAPIView.as_view(), name='usuario-actual'),

    # --- Gestión de Transacciones ---
    # 1) Crear una Transacción (con lista de items y descuento global):
    path('transacciones/', TransaccionCreateAPIView.as_view(), name='transaccion-create'),
    # 2) Obtener detalle de transacción (incluye items, totales y descuento):
    path('transacciones/<int:pk>/', TransaccionDetailAPIView.as_view(), name='transaccion-detail'),
    # 3) Confirmar la transacción (verificar stock y descontar):
    path('transacciones/<int:pk>/confirmar/', ConfirmarTransaccionAPIView.as_view(), name='transaccion-confirmar'),

    # --- CRUD Productos ---
    path('productos/', ProductoListCreateAPIView.as_view(), name='producto-list-create'),
    path('productos/<int:pk>/', ProductoDetailAPIView.as_view(), name='producto-detail'),

    # --- CRUD Stocks ---
    path('stocks/', StockListCreateAPIView.as_view(), name='stock-list-create'),
    path('stocks/<int:pk>/', StockDetailAPIView.as_view(), name='stock-detail'),
]
