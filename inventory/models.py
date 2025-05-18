from django.db import models

class Product(models.Model):
    id = models.AutoField(primary_key=True)
    code     = models.CharField(max_length=64, unique=True)
    name     = models.CharField(max_length=200)
    quantity = models.IntegerField(default=0)

    class Meta:
        db_table = 'products'


    def __str__(self):
        return f"{self.code} – {self.name}"
