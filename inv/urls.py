from django.urls import path
from .views import ProductoListView, buscar_productos
from . import views


app_name = 'inv'

urlpatterns = [
    path('', ProductoListView.as_view(), name='producto_list'),  # Ruta para la URL raíz
    path('productos/', ProductoListView.as_view(), name='producto_list'),
    path('productos/ajax/', views.producto_list_ajax, name='producto_list_ajax'),
    path('productos/crear/', views.producto_crear, name='producto_crear'),
    path('productos/editar/<int:pk>/', views.producto_editar, name='producto_editar'),
    path('productos/eliminar/<int:pk>/', views.producto_eliminar, name='producto_eliminar'),
    path('productos/mover/<int:pk>/', views.producto_mover, name='producto_mover'),
    path('buscar_productos/', buscar_productos, name='buscar_productos'),
    path('buscar_productos_autocomplete/', views.buscar_productos_autocomplete, name='buscar_productos_autocomplete'),
    
]
