# ManuMarket

Repositorio para el proyecto de punto de ventas y gestión de inventario de *ManuMarket*.

---

## Preparar el backend (Django + PostgreSQL)

1. Posicionarse en el directorio de backend y activar entorno virtual  

    ```powershell

    cd backend
    python -m venv env
    .\env\Scripts\Activate.ps1

    pip install -r requirements.txt

    ```

2. Crear el fichero *.env* con tus credenciales de conexión (junto a docker-compose.yml en /backend)

    ```dotenv

    ALLOWED_HOSTS=localhost,127.0.0.1
    SECRET_KEY=manumarket
    DEBUG=True
    DATABASE_ENGINE=django.db.backends.postgresql
    DATABASE_NAME=manumarket
    DATABASE_USER=postgres
    DATABASE_PASSWORD=postgres
    DATABASE_HOST=db
    DATABASE_PORT=5432

    ```

3. Levantar los contenedores

   ```powershell
   # Limpiar restos de ejecuciones anteriores
   docker-compose down --volumes --remove-orphans

   docker-compose up --build -d
   docker ps

   ```

4. API en Swagger

   - Ingresar a: <http://localhost:8001/swagger/>

---

## Preparar el frontend (Astro)

1. Posicionamos en el directorio **/frontend** e instalamos las dependencias.

    ```powershell

    cd ..
    cd frontend
    npm install
    npm install astro

    ```

2. Levantamos el servidor **Astro**

    ```powershell

    npm run dev

    ```

---

### Credenciales y comandos varios

```bash

npm install dotenv --save-dev

username='admin'
password='admin123'

username='trabajador',
password='worker123'

```

---

## HU2

Este repositorio contiene la implementación de la Historia de Usuario HU02: un sistema de Punto de Venta que permite escanear productos mediante un lector de código de barras, agregar ítems a una transacción, mostrar lista de productos y total, y confirmar la venta.

## Tecnologías usadas

- **Backend**: Django 5.2, Django REST Framework, django-cors-headers
- **Frontend**: Astro, Tailwind CSS
- **Entorno**: Python 3.12+, Node.js 18+

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

- Api django <http://localhost:8000/api/>

- front <http://localhost:3000/api/>

### AGREGAR PRODUCTOS (estando dentro de env)

   ```powershell

   python manage.py shell
   from ventas.models import Producto
   Producto.objects.create(codigo='1234567890123', nombre='Coca-Cola 500ml', precio=1.25)
   Producto.objects.create(codigo='9876543210987', nombre='Agua Mineral 1L', precio=0.95)

   ```

### Endpoints disponibles

- `POST   /api/transacciones/` → crea nueva transacción (vacía)
- `GET    /api/productos/`       → lista de productos
- `GET    /api/productos/<codigo>/` → detalles de un producto
- `POST   /api/transacciones/<id>/agregar_item/` → agrega un ítem (requiere JSON `{ "codigo": ..., "cantidad": ... }`)
- `POST   /api/transacciones/<id>/confirmar/`   → confirma la venta (opcional JSON `{ "exito": true }`)

## Uso local

1. Levanta backend (`:8000`) y frontend (`:3000`).
2. En el navegador, ve al front y usando un lector de código de barras (o manualmente) escanea productos.
3. Verifica en Django admin o en `/api/transacciones/` que el estado cambie correctamente.

---
