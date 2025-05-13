from django.urls import path
from .views import pos_interface

urlpatterns = [
    path('api/pos/', pos_interface, name='pos_interface'),
]