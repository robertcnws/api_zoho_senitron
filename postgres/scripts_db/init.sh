#!/bin/bash
set -e

# Lista de bases de datos a crear
DBS=("api_zoho_senitron_dev_db" "api_zoho_senitron_qa_db" "api_zoho_senitron_prod_db")

for DB in "${DBS[@]}"; do
    echo "Verificando si la base de datos '$DB' existe..."
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "postgres" <<-EOSQL
        SELECT 1 FROM pg_database WHERE datname = '$DB';
    EOSQL

    EXISTS=$(psql -tAc "SELECT 1 FROM pg_database WHERE datname='$DB'" | grep -c 1)

    if [ $EXISTS -eq 0 ]; then
        echo "Creando la base de datos '$DB'..."
        createdb -U "$POSTGRES_USER" "$DB"
    else
        echo "La base de datos '$DB' ya existe. Saltando..."
    fi
done
