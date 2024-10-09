from django.urls import path
from .views import ProductoListView, buscar_productos

app_name = 'inv'

urlpatterns = [
    path('', ProductoListView.as_view(), name='producto_list'),  # Ruta para la URL raíz
    path('productos/', ProductoListView.as_view(), name='producto_list'),
    path('buscar_productos/', buscar_productos, name='buscar_productos'),
]
