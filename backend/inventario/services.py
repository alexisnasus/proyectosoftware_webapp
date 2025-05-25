from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from .models import Stock

@transaction.atomic
def actualizar_stock(producto_id, cantidad_alfa):
    # Bloquea la fila específica para evitar condiciones de carrera
    stock = Stock.objects.select_for_update().get(producto_id=producto_id)

    nueva_cantidad = stock.cantidad + cantidad_alfa
    if nueva_cantidad < 0:
        raise ValueError("No hay suficiente stock para restar esa cantidad.")

    stock.cantidad = nueva_cantidad
    stock.save()
    return stock
