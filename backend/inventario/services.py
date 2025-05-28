from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from .models import Stock

@transaction.atomic
def agregar_stock(producto_id, cantidad):
    """Solo permite agregar cantidades positivas al stock"""
    if cantidad <= 0:
        raise ValueError("La cantidad a agregar debe ser positiva")
    
    stock = Stock.objects.select_for_update().get(producto_id=producto_id)
    stock.cantidad = F('cantidad') + cantidad
    stock.save()
    return Stock.objects.get(pk=stock.pk)  # Refresca los valores

@transaction.atomic
def quitar_stock(producto_id, cantidad):
    """Solo permite quitar cantidades positivas del stock"""
    if cantidad <= 0:
        raise ValueError("La cantidad a quitar debe ser positiva")
    
    stock = Stock.objects.select_for_update().get(producto_id=producto_id)
    if stock.cantidad < cantidad:
        raise ValueError("No hay suficiente stock para restar esa cantidad")
    
    stock.cantidad = F('cantidad') - cantidad
    stock.save()
    return Stock.objects.get(pk=stock.pk)  # Refresca los valores