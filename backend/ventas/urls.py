from rest_framework.routers import DefaultRouter
from .views import ProductoViewSet, TransaccionViewSet

router = DefaultRouter()
router.register('transacciones', TransaccionViewSet, basename='transaccion')
router.register(r'productos', ProductoViewSet, basename='producto')

urlpatterns = router.urls