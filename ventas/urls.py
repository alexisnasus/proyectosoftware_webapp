from django.urls import path
from . import views

app_name = 'ventas'

urlpatterns = [
    path('nueva/', views.NuevaVentaView.as_view(), name='venta_nueva'),
    path('detalle/<int:venta_id>/', views.VentaDetalleView.as_view(), name='venta_detalle'),
    path('obtener_stock/', views.obtener_stock, name='obtener_stock'),  # Añadir esta línea
    path('devolver/<int:detalle_venta_id>/', views.DevolverProductoView.as_view(), name='devolver_producto'),
]
