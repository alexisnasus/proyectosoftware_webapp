# Punto de Venta WebApp

Este repositorio contiene la implementación de la Historia de Usuario HU02: un sistema de Punto de Venta que permite escanear productos mediante un lector de código de barras, agregar ítems a una transacción, mostrar lista de productos y total, y confirmar la venta.

## Tecnologías usadas

* **Backend**: Django 5.2, Django REST Framework, django-cors-headers
* **Frontend**: Astro, Tailwind CSS
* **Entorno**: Python 3.12+, Node.js 18+

## Estructura del proyecto

```
/ (raíz del repo)
├─ .venv/                      # Entorno virtual de Python
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

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate      # Linux/Mac
   .\.venv\Scripts\Activate.ps1 # Windows PowerShell
   ```
2. Instala dependencias:

   ```bash
   pip install django djangorestframework django-cors-headers
   ```
3. Configura `backend/backend/settings.py`:

   * Añade a `INSTALLED_APPS`: `'rest_framework', 'corsheaders', 'ventas'`
   * Asegúrate de incluir en `MIDDLEWARE`: `'corsheaders.middleware.CorsMiddleware'` antes de `CommonMiddleware`.
   * Añade al final:

     ```python
     CORS_ALLOWED_ORIGINS = [
       'http://localhost:3000',
       'http://127.0.0.1:3000',
     ]
     ```
4. Crea tablas en la base de datos:

   ```bash
   cd backend
   python manage.py makemigrations ventas
   python manage.py migrate
   ```
5. (Opcional) Crea superusuario:

   ```bash
   python manage.py createsuperuser
   ```
6. Arranca el servidor:

   ```bash
   python manage.py runserver 8000
   ```

### Endpoints disponibles

* `POST   /api/transacciones/` → crea nueva transacción (vacía)
* `GET    /api/productos/`       → lista de productos
* `GET    /api/productos/<codigo>/` → detalles de un producto
* `POST   /api/transacciones/<id>/agregar_item/` → agrega un ítem (requiere JSON `{ "codigo": ..., "cantidad": ... }`)
* `POST   /api/transacciones/<id>/confirmar/`   → confirma la venta (opcional JSON `{ "exito": true }`)

## Configuración del frontend (Astro + Tailwind) [TO DO]

1. En un terminal, ingresa a la carpeta frontend:

   ```bash
   cd frontend
   ```
2. Instala dependencias y configura Tailwind:

   ```bash
   npm install
   npm install -D tailwindcss postcss autoprefixer
   npx tailwindcss init -p
   ```

   Ajusta `tailwind.config.cjs`:

   ```js
   module.exports = {
     content: ['./src/**/*.{astro,js,ts,jsx,tsx,html}'],
     theme: { extend: {} },
     plugins: []
   };
   ```

   Importa en `src/styles/global.css`:

   ```css
   @tailwind base;
   @tailwind components;
   @tailwind utilities;
   ```
3. Arranca el servidor de desarrollo:

   ```bash
   npm run dev
   ```
4. Abre `http://localhost:3000` y prueba el flujo:

   * Escanear (o escribir) un código de barras + Enter
   * Ver lista de productos y total actualizado
   * Pulsar “Confirmar Venta” para marcar el estado

## Uso local

1. Levanta backend (`:8000`) y frontend (`:3000`).
2. En el navegador, ve al front y usando un lector de código de barras (o manualmente) escanea productos.
3. Verifica en Django admin o en `/api/transacciones/` que el estado cambie correctamente.


## Contribuciones

Las contribuciones son bienvenidas: abre issues o pull requests.

## Licencia

Este proyecto está bajo la licencia MIT. ¡Siéntete libre de usarlo y adaptarlo!
