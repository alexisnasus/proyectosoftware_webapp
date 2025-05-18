# backend/ventas/urls.py
from rest_framework.routers import DefaultRouter
from .views import ProductoViewSet, TransaccionViewSet

router = DefaultRouter()
router.register('productos', ProductoViewSet, basename='producto')
router.register('transacciones', TransaccionViewSet, basename='transaccion')

urlpatterns = router.urls
