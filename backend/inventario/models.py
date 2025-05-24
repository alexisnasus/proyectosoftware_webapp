from django.db import models

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

