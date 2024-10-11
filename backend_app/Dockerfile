FROM python:3.12

ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --upgrade pip
RUN pip install gunicorn
RUN pip install -r requirements.txt

# Instalar herramientas necesarias incluyendo cron
RUN apt-get update && apt-get install -y wget gnupg2 lsb-release

# Agregar repositorio de PostgreSQL
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" | tee /etc/apt/sources.list.d/pgdg.list

# Actualizar e instalar dependencias
RUN apt-get update && apt-get install -y postgresql-client-16

# Copia el contenido del directorio al contenedor
COPY . /app/

# Expose port 8000 for the Django application
EXPOSE 8000

# Ejecuta el script de inicialización y luego arranca Gunicorn y cron
CMD ["sh", "-c", "python manage.py makemigrations && python manage.py migrate && python init_scripts.py && gunicorn --bind 0.0.0.0:8000 _api_zoho_senitron.wsgi:application"]
