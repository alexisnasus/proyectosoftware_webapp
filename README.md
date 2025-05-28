# ManuMarket

Repositorio para el proyecto de punto de ventas y gestión de inventario de *ManuMarket*.

## Tecnologías usadas

- **Backend**: Django 5.2, Django REST Framework, django-cors-headers
- **Frontend**: Astro, Tailwind CSS
- **Entorno**: Python 3.12+, Node.js 18+

---

## Levantar app

1. Activar entorno virtual 👻  

    ```powershell

    python -m venv env
    .\env\Scripts\Activate.ps1

    pip install -r requirements.txt
     # source env/bin/activate (mac/linux)

    ```

2. Levantar los contenedores

   ```powershell
   # a) Limpiar restos de ejecuciones anteriores
   docker-compose down --volumes --remove-orphans
   docker-compose up --build -d
   
   # El problema más común es que se pueden tener contenedores repetidos (sin importar si están detenidos o no)
   # Detener de forma manual: docker rm {nombre del contenedor}


   # b) Chequee que están los contenedores corriendo:
   docker ps

   # c) Hacer migraciones
   docker-compose exec users_api python manage.py migrate
   docker-compose exec users_api python manage.py makemigrations
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
