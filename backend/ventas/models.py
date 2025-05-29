from django.db import models
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('ADMIN', 'Administrador'),
        ('EMPLOYEE', 'Empleado'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, null=False, blank=False)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Producto(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'producto'

    def __str__(self):
        return f"{self.codigo} – {self.nombre}"

class Stock(models.Model):
    producto = models.OneToOneField(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=0)

    class Meta:
        db_table = 'stock'

    def __str__(self):
        return f"Stock({self.producto.codigo}): {self.cantidad}"

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
