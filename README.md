# ManuMarket

Repositorio para el proyecto de punto de ventas y gestión de inventario de *ManuMarket*.

## Tecnologías usadas

- **Backend**: Django 5.2, Django REST Framework, django-cors-headers
- **Frontend**: Tailwind CSS
- **Entorno**: Python 3.12+, Node.js 18+
holaohola
---

## Levantar app

1. Activar entorno virtual 👻  

    ```powershell

    python -m venv env
    .\env\Scripts\Activate.ps1 #source env/bin/activate (mac/linux)
    pip install -r requirements.txt

    ```

2. Levantar los contenedores

   ```powershell

   # Limpiar restos de ejecuciones anteriores
   docker-compose down --volumes --remove-orphans

   # levantar los contenedores
   docker-compose up --build -d
   
   #chequear si los contenedores están corriendo
   docker ps

   #Hacer migraciones
   docker-compose exec ventas_api python manage.py makemigrations ventas
   docker-compose exec ventas_api python manage.py migrate
   
   #crear las credenciales
   docker-compose exec ventas_api python manage.py createsuperuser

   ```

3. URL´L

   - Test de API: <http://localhost:8000/swagger/>
   - front-node: <http://localhost:3000/>

---

### Credenciales y comandos varios

  ```bash
  
  username='admin'
  password='admin123'

  username='trabajador',
  password='worker123'

  ```

---
