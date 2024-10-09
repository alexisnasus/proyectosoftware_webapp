from django.urls import path
from . import views

app_name = 'ventas'

urlpatterns = [
    path('nueva/', views.NuevaVentaView.as_view(), name='venta_nueva'),
    path('detalle/<int:venta_id>/', views.VentaDetalleView.as_view(), name='venta_detalle'),
]
