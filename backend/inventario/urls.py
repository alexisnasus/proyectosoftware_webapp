from rest_framework.routers import DefaultRouter
from .views import ProductoViewSet, StockViewSet
from django.urls import path, include

router = DefaultRouter()
router.register(r'productos', ProductoViewSet, basename='producto')
router.register(r'stock', StockViewSet, basename='stock')

urlpatterns = [
    path('', include(router.urls)),
]
