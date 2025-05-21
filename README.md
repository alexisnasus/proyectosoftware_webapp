# Punto de Venta WebApp

Este repositorio contiene la implementación de la Historia de Usuario HU02: un sistema de Punto de Venta que permite escanear productos mediante un lector de código de barras, agregar ítems a una transacción, mostrar lista de productos y total, y confirmar la venta.

## Tecnologías usadas

* **Backend**: Django 5.2, Django REST Framework, django-cors-headers
* **Frontend**: Astro, Tailwind CSS
* **Entorno**: Python 3.12+, Node.js 18+

## Estructura del proyecto

```txt

/ (raíz del repo)
├─ env/                      # Entorno virtual de Python
├─ backend/                    # Proyecto Django
│  ├─ backend/                 # Configuración global (settings, urls)
│  ├─ ventas/                  # App de ventas (modelos, views, serializers)
│  ├─ manage.py
│  └─ db.sqlite3
└─ frontend/                   # Proyecto Astro + Tailwind
   ├─ src/
   ├─ public/
   ├─ astro.config.mjs
   └─ package.json

```

## Configuración del backend (Django)

1. Abre un terminal en la raíz del repo y crea/activa el virtualenv:

   ```powershell

   python -m venv env
   .\env\Scripts\Activate.ps1

   ```

2. Instala dependencias:

   ```bash

   pip install django djangorestframework django-cors-headers

   ```

3. Crea tablas en la base de datos:

   ```bash

   cd backend
   python manage.py makemigrations ventas
   python manage.py migrate

   ```

4. (Opcional) Crea superusuario:

   ```bash

   python manage.py createsuperuser

   ```

5. Arranca el servidor backend:

   ```powershell

   python manage.py runserver 8000

   ```

6. Levantar front

   ```powershell

   python -m http.server 3000

   ```

### URL disponibles

* Api django <http://localhost:8000/api/>

* front <http://localhost:3000/api/>

### AGREGAR PRODUCTOS (estando dentro de env)

   ```powershell

   python manage.py shell
   from ventas.models import Producto
   Producto.objects.create(codigo='1234567890123', nombre='Coca-Cola 500ml', precio=1.25)
   Producto.objects.create(codigo='9876543210987', nombre='Agua Mineral 1L', precio=0.95)

   ```

### Endpoints disponibles

* `POST   /api/transacciones/` → crea nueva transacción (vacía)
* `GET    /api/productos/`       → lista de productos
* `GET    /api/productos/<codigo>/` → detalles de un producto
* `POST   /api/transacciones/<id>/agregar_item/` → agrega un ítem (requiere JSON `{ "codigo": ..., "cantidad": ... }`)
* `POST   /api/transacciones/<id>/confirmar/`   → confirma la venta (opcional JSON `{ "exito": true }`)

## Uso local

1. Levanta backend (`:8000`) y frontend (`:3000`).
2. En el navegador, ve al front y usando un lector de código de barras (o manualmente) escanea productos.
3. Verifica en Django admin o en `/api/transacciones/` que el estado cambie correctamente.
