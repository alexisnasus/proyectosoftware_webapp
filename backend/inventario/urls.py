from django.urls import path
from .views import ProductoView, ProductoDetalleView, StockView

urlpatterns = [
    path('productos/', ProductoView.as_view(), name='producto-lista'),
    path('productos/<int:pk>/', ProductoDetalleView.as_view(), name='producto-detalle'),
    path('stock/', StockView.as_view(), name='stock'),
]
