# Crea y activa un virtualenv (recomendado)
python3 -m venv .venv
source .venv/bin/activate

# Instala Django, Django REST Framework y CORS headers
pip install django djangorestframework django-cors-headers

# Crea el proyecto y la app “ventas”
django-admin startproject backend
cd backend
python manage.py startapp ventas
