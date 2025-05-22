from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Producto, Transaccion, LineaVenta
from .serializers import ProductoSerializer, TransaccionSerializer
from django.utils import timezone

class ProductoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    lookup_field = 'codigo'

class TransaccionViewSet(viewsets.ModelViewSet):
    queryset = Transaccion.objects.all()
    serializer_class = TransaccionSerializer

    @action(detail=True, methods=['post'])
    def agregar_item(self, request, pk=None):
        tx = self.get_object()
        codigo = request.data.get('codigo')
        cantidad = int(request.data.get('cantidad', 1))
        try:
            prod = Producto.objects.get(codigo=codigo)
        except Producto.DoesNotExist:
            return Response({'error':'Producto no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        LineaVenta.objects.create(transaccion=tx, producto=prod, cantidad=cantidad)
        return Response(self.get_serializer(tx).data)
    
    @action(detail=True, methods=['post'])
    def confirmar(self, request, pk=None):
        tx = self.get_object()
        # opcional: acepta {"exito":false} para fallback
        exito = request.data.get('exito', True)
        tx.estado = 'CONFIRMADA' if exito else 'FALLIDA'
        tx.confirmado_en = timezone.now()
        tx.save()
        return Response(self.get_serializer(tx).data)