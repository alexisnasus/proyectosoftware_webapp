from django import forms
from django.forms import inlineformset_factory
from .models import Producto, Inventario

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'codigo_barras', 'precio', 'seccion', 'subseccion']

# Crear un FormSet para Inventario
InventarioFormSet = inlineformset_factory(
    Producto,
    Inventario,
    fields=['ubicacion', 'cantidad', 'cantidad_minima'],
    extra=1,
    can_delete=True,
)
