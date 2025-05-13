from django.urls import path
from .views import get_products

urlpatterns = [
    path('api/products/', get_products, name='get_products'),
]