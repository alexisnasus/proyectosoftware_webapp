from django.db import models

class Sale(models.Model):
    id = models.AutoField(primary_key=True)
    product  = models.ForeignKey(
        'inventory.Product',
        db_column='product_id',
        on_delete=models.PROTECT
    )
    quantity = models.IntegerField()
    sold_at  = models.DateTimeField()

    class Meta:
        db_table = 'sales'


    def __str__(self):
        return f"Venta {self.id}: {self.quantity}×{self.product.code}"
