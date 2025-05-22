# ManuMarket

Repositorio para el proyecto de punto de ventas y gestión de inventario de *ManuMarket*.

---

## HU1

### 1. Configuración del entorno local

Iniciamos una terminal, estando en la carpeta root del proyecto.

```powershell
python -m venv env
.\env\Scripts\Activate.ps1

pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Preparar y levantar los contenedores Docker

```powershell
# Limpiar restos de ejecuciones anteriores
docker-compose down --volumes --remove-orphans

docker-compose up --build -d
docker ps

```

### 3. Detener y limpiar todo

```powershell

docker-compose down --volumes --remove-orphans

```

### API en Swagger

<http://localhost:8001/swagger/>

---

## HU2

### 1

---

## **HU7**

### Preparar el backend (Django + PostgreSQL)

1. Posicionarse en el directorio de backend y activar entorno virtual  

    ```powershell

    cd backend
    python -m venv env
    .\env\Scripts\Activate.ps1

    pip install -r requirements.txt

    ```

2. Crear el fichero *.env* con tus credenciales de conexión (junto a docker-compose.yml)

    ```dotenv

    SECRET_KEY=manumarket
    DEBUG=True

    DATABASE_ENGINE=django.db.backends.postgresql
    DATABASE_NAME=manumarket
    DATABASE_USER=postgres
    DATABASE_PASSWORD=postgres
    DATABASE_HOST=db
    DATABASE_PORT=5432

    ```

3. Preparar y levantar los contenedores Docker

    ```powershell
    # Limpiar restos de ejecuciones anteriores
    docker-compose down --volumes --remove-orphans

    docker-compose up --build -d
    docker ps

    ```

4. Comprobar endpoint de login

    ```powershell
    
    Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/login/" -Method POST -Headers @{ "Content-Type" = "application/json" } -Body (@{ username = 'admin'; password = 'admin123' } | ConvertTo-Json)

    ```

### Preparar el frontend (Astro)

1. Posicionamos en la raíz del proyecto e instalamos las dependencias.

    ```powershell

    cd ..
    npm install

    ```

2. Arrancamos **Astro**

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
