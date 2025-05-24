# ManuMarket

Repositorio para el proyecto de punto de ventas y gestión de inventario de *ManuMarket*.

## Tecnologías usadas

- **Backend**: Django 5.2, Django REST Framework, django-cors-headers
- **Frontend**: Astro, Tailwind CSS
- **Entorno**: Python 3.12+, Node.js 18+

---

## Preparar el backend (Django + PostgreSQL)

1. Posicionarse en el directorio de backend y activar entorno virtual  

    ```powershell

    python -m venv env
    .\env\Scripts\Activate.ps1

    pip install -r requirements.txt

    ```

2. Levantar los contenedores

   ```powershell
   # Limpiar restos de ejecuciones anteriores
   docker-compose down --volumes --remove-orphans

   docker-compose up --build -d
   docker ps

   ```

3. URL´L

   - Test de API: <http://localhost:8001/swagger/>
   - front: <http://localhost:4321/>

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
