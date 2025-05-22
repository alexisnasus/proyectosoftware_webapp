from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Sale
from .serializers import SaleSerializer
from drf_yasg.utils import swagger_auto_schema

class SaleCrearView(APIView):
    @swagger_auto_schema(request_body=SaleSerializer)
    def post(self, request):
        serializer = SaleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SaleConsultarView(APIView):
    def get(self, request):
        ventas = Sale.objects.all()
        serializer = SaleSerializer(ventas, many=True)
        return Response(serializer.data)

class SaleObtenerView(APIView):
    def get(self, request, pk):
        venta = get_object_or_404(Sale, pk=pk)
        serializer = SaleSerializer(venta)
        return Response(serializer.data)

class SaleActualizarView(APIView):
    http_method_names = ['put', 'head', 'options']
    @swagger_auto_schema(request_body=SaleSerializer)
    def put(self, request, pk):
        venta = get_object_or_404(Sale, pk=pk)
        serializer = SaleSerializer(venta, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SaleBorrarView(APIView):
    def delete(self, request, pk):
        venta = get_object_or_404(Sale, pk=pk)
        venta.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
