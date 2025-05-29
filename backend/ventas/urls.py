from django.urls import path, include
from .views import (
    MyTokenObtainPairView,
    LogoutView,
    MeView,
    ConcretarVentaAPIView,
    ProductoListCreateAPIView,
    ProductoDetailAPIView,
    StockListCreateAPIView,
    StockDetailAPIView,
)
from rest_framework_simplejwt.views import TokenRefreshView

auth_urls = [
    path('login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('logout/', LogoutView.as_view(), name='auth_logout'),
    path('me/', MeView.as_view(), name='auth_me'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

urlpatterns = [
    path('user/', include(auth_urls)),
    path('venta/concretar/', ConcretarVentaAPIView.as_view(), name='venta-concretar'),
    path('productos/', ProductoListCreateAPIView.as_view(), name='producto-list-create'),
    path('productos/<int:pk>/', ProductoDetailAPIView.as_view(), name='producto-detail'),
    path('stocks/', StockListCreateAPIView.as_view(), name='stock-list-create'),
    path('stocks/<int:pk>/', StockDetailAPIView.as_view(), name='stock-detail'),
]
