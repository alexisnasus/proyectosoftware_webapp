# Dockerfile
FROM python:3.10-slim

# Variables de entorno para evitar bytecode y buffering
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Directorio de trabajo en el contenedor
WORKDIR /code

# Copiamos requisitos e instalamos
COPY requirements.txt /code/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copiamos todo el proyecto
COPY . /code/

# Puerto que exponemos para Django
EXPOSE 8000

# Comando por defecto – en dev usamos runserver
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
