from django.db import models
from inventario.models import Producto
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
    descuento_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = 'transaccion'

    @property
    def total(self):
        return sum(item.subtotal for item in self.item_set.all())
    
    @property
    def total_final(self):
        return self.total - self.descuento_total

class Item(models.Model):
    transaccion = models.ForeignKey(Transaccion, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = 'item'

    @property
    def subtotal(self):
        return (self.producto.precio - self.descuento) * self.cantidad
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.actualizar_descuento_transaccion()
    
    def actualizar_descuento_transaccion(self):
        transaccion = self.transaccion
        transaccion.descuento_total = sum(item.descuento * item.cantidad for item in transaccion.item_set.all())
        transaccion.save()