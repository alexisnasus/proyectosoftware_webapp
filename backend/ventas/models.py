from django.db import models
import uuid

class Producto(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.nombre

class Transaccion(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADA','Confirmada'),
        ('FALLIDA',   'Fallida'),
    ]
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creado_en   = models.DateTimeField(auto_now_add=True)
    confirmado_en = models.DateTimeField(null=True, blank=True)
    estado      = models.CharField(max_length=10, choices=ESTADOS, default='PENDIENTE')

    @property
    def total(self):
        return sum(lv.subtotal for lv in self.lineaventa_set.all())

class LineaVenta(models.Model):
    transaccion = models.ForeignKey(Transaccion, on_delete=models.CASCADE)
    producto    = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad    = models.PositiveIntegerField(default=1)

    @property
    def subtotal(self):
        return self.producto.precio * self.cantidad