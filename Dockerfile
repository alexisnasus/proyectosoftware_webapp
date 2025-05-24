FROM python:3.10-slim

# Instalar dependencias del sistema necesarias
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Evitar creación de archivos pyc y habilitar logs en consola
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivo de requerimientos y backend
COPY requirements.txt /app/
COPY backend /app/

# Instalar dependencias de Python
RUN pip install --upgrade pip && pip install -r requirements.txt

# Exponer el puerto del servidor Django
EXPOSE 8000

# Comando para levantar el servidor Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
