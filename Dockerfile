# Dockerfile
FROM python:3.10-slim

# Instalar dependencias del sistema para psycopg2
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Variables de entorno para evitar bytecode y buffering
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Directorio de trabajo en el contenedor
WORKDIR /code

# Copiar e instalar requisitos Python
COPY requirements.txt /code/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copiar todo el proyecto
COPY . /code/

# Exponer el puerto de Django
EXPOSE 8000

# Comando por defecto (se puede sobrescribir en docker-compose)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
