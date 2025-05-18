from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Product
from .serializers import ProductSerializer
from drf_yasg.utils import swagger_auto_schema

class ProductCrearView(APIView):
    @swagger_auto_schema(request_body=ProductSerializer)
    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProductConsultarView(APIView):
    def get(self, request):
        productos = Product.objects.all()
        serializer = ProductSerializer(productos, many=True)
        return Response(serializer.data)

class ProductObtenerView(APIView):
    def get(self, request, pk):
        producto = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(producto)
        return Response(serializer.data)

class ProductActualizarView(APIView):
    http_method_names = ['put', 'head', 'options']
    @swagger_auto_schema(request_body=ProductSerializer)
    def put(self, request, pk):
        producto = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(producto, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProductBorrarView(APIView):
    def delete(self, request, pk):
        producto = get_object_or_404(Product, pk=pk)
        producto.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
