# ManuMarket  
Repositorio para el proyecto de punto de ventas y gestión de inventario de *ManuMarket*.

---

## 1. Configuración del entorno local

```powershell
python -m venv env #en caso de error utilizar los siguientes comandos
.\env\Scripts\Activate.ps1

pip install --upgrade pip
pip install -r requirements.txt
```

---

## 2. Preparar y levantar los contenedores Docker

```powershell
# (Opcional) Limpiar restos de ejecuciones anteriores
docker-compose down --volumes --remove-orphans
docker volume prune -f

# Construir imágenes y arrancar en segundo plano
docker-compose up --build -d

# otro
docker compose build --no-cache
docker compose up --force-recreate -d


# Verificar estado de los contenedores
docker ps

```

---

## 3. Ejecutar migraciones dentro de los microservicios

```powershell
# Migraciones para inventory_api
docker-compose exec inventory_api python manage.py makemigrations
docker-compose exec inventory_api python manage.py migrate

# Migraciones para sales_api
docker-compose exec sales_api python manage.py makemigrations
docker-compose exec sales_api python manage.py migrate

```
---

## 4. Detener y limpiar todo

```powershell

docker-compose down --volumes --remove-orphans

```
## 5. Casos de errores y posibles soluciones

``` Error en postman "socket hang up"

docker compose down     # si las imagenes de docker se estan ejecutando.

docker-compose up --build -d    # Para volver a iniciar las imagenes o contenedores de docker.

docker ps    # revisar si los contenedores se estan ejecutando

# En caso de que el error sea porque los contenedores o imagenes de docker estan apagados o el comando de encendido no funciona
# Ejecutar docker de manera manual.

