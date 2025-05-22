# Dockerfile (en backend/)
FROM python:3.10-slim

# no escriba pyc, output en streaming
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# copiamos solo requirements primero (para cache)
COPY requirements.txt /app/
RUN pip install --upgrade pip \
 && pip install -r requirements.txt

# copiamos todo el código
COPY . /app/

# exponemos el puerto Django
EXPOSE 8000

# comando por defecto
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
