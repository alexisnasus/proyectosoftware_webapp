from django.urls import path
from .views import (
    SaleCrearView,
    SaleConsultarView,
    SaleObtenerView,
    SaleActualizarView,
    SaleBorrarView,
)

urlpatterns = [
    path('sales/crear/',       SaleCrearView.as_view(),    name='sale-crear'),
    path('sales/consultar/',   SaleConsultarView.as_view(),name='sale-consultar'),
    path('sales/obtener/<int:pk>/',    SaleObtenerView.as_view(),   name='sale-obtener'),
    path('sales/actualizar/<int:pk>/', SaleActualizarView.as_view(), name='sale-actualizar'),
    path('sales/borrar/<int:pk>/',     SaleBorrarView.as_view(),    name='sale-borrar'),
]
