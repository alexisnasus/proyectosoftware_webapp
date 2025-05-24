from django.db import models
from inventario.models import Producto  # usamos el modelo centralizado
import uuid

class Transaccion(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADA','Confirmada'),
        ('FALLIDA',   'Fallida'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creado_en = models.DateTimeField(auto_now_add=True)
    confirmado_en = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='PENDIENTE')

    class Meta:
        db_table = 'transaccion'

    @property
    def total(self):
        return sum(item.subtotal for item in self.item_set.all())

class Item(models.Model):
    transaccion = models.ForeignKey(Transaccion, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'item'

    @property
    def subtotal(self):
        return self.producto.precio * self.cantidad
