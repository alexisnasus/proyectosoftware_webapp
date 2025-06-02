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
    source env/bin/activate
    pip install -r requirements.txt
     # source env/bin/activate (mac/linux)

    ```

2. Levantar los contenedores

   ```powershell
   # Limpiar restos de ejecuciones anteriores
   docker-compose down --volumes --remove-orphans

   docker-compose up --build -d
   docker ps

   #Hacer migraciones
   docker-compose exec ventas_api python manage.py makemigrations ventas
   docker-compose exec ventas_api python manage.py migrate
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
