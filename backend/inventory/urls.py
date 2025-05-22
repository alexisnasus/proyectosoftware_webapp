from django.urls import path
from .views import (
    ProductCrearView,
    ProductConsultarView,
    ProductObtenerView,
    ProductActualizarView,
    ProductBorrarView,
)

urlpatterns = [
    path('items/crear/',      ProductCrearView.as_view(),     name='product-crear'),
    path('items/consultar/',  ProductConsultarView.as_view(), name='product-consultar'),
    path('items/obtener/<int:pk>/',   ProductObtenerView.as_view(),   name='product-obtener'),
    path('items/actualizar/<int:pk>/',ProductActualizarView.as_view(),name='product-actualizar'),
    path('items/borrar/<int:pk>/',    ProductBorrarView.as_view(),    name='product-borrar'),
]
