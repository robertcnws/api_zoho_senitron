# Usa una imagen base ligera de Python 3.12
FROM python:3.12-slim

# Variables de entorno para evitar problemas de buffering y configurar el PYTHONPATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instala dependencias del sistema necesarias para compilar psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    wget \
    gnupg2 \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Agrega el repositorio de PostgreSQL y actualiza las listas de paquetes
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - \
    && echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" | tee /etc/apt/sources.list.d/pgdg.list \
    && apt-get update && apt-get install -y --no-install-recommends postgresql-client-16 \
    && rm -rf /var/lib/apt/lists/*

# Copia el archivo de requisitos al directorio de trabajo
COPY requirements.txt /app/

# Actualiza pip e instala las dependencias de Python
RUN pip install --upgrade pip \
    && pip install gunicorn uvicorn \
    && pip install -r requirements.txt

# Copia el resto del código de la aplicación al contenedor
COPY . /app/

# Expone el puerto 8000 para la aplicación Django
EXPOSE 8000

# Comando para ejecutar la aplicación usando Gunicorn y Uvicorn
CMD ["sh", "-c", "python manage.py makemigrations && python manage.py migrate && python manage.py collectstatic --no-input && python init_scripts.py && gunicorn api_project_zoho_senitron.asgi:application -w 3 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000"]
