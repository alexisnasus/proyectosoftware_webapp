import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def pos_interface(request):
    try:
        # Simular comunicación con inventory service
        inventory_response = requests.get('http://inventory:8000/api/products/')
        return Response({
            "status": "POS activo",
            "inventory_data": inventory_response.json()
        })
    except Exception as e:
        return Response({"error": str(e)}, status=500)