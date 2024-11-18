# Usa una imagen base ligera de Python 3.12
FROM python:3.12-slim

# Variables de entorno para evitar problemas de buffering y configurar el PYTHONPATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instala dependencias del sistema necesarias para compilar psycopg2 y agregar el repositorio de PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    wget \
    gnupg \
    ca-certificates \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Agrega la clave GPG de PostgreSQL de forma compatible con Debian 12
RUN mkdir -p /etc/apt/keyrings \
    && wget -qO- https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor > /etc/apt/keyrings/postgresql.gpg

# Agrega el repositorio de PostgreSQL usando el método 'signed-by'
RUN echo "deb [signed-by=/etc/apt/keyrings/postgresql.gpg] http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list

# Actualiza los paquetes e instala libpq-dev y postgresql-client-16
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    postgresql-client-16 \
    && rm -rf /var/lib/apt/lists/*

# Verifica que pg_config está disponible
RUN which pg_config

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
