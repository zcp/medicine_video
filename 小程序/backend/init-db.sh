#!/bin/bash
set -e

# Function to check if a database exists
database_exists() {
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname=postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$1'" | grep -q 1
}

# Read database names from environment variables
LIVE_CORE_DB=${LIVE_CORE_DB:-live_core_test}
MEDIA_DOWNLOAD_DB=${MEDIA_DOWNLOAD_DB:-media_download_test}
USERS_SERVICE_DB=${USERS_SERVICE_DB:-users_service_test}

# Create LIVE_CORE_DB database if it does not exist
if ! database_exists "$LIVE_CORE_DB"; then
    echo "Creating $LIVE_CORE_DB database..."
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
        CREATE DATABASE $LIVE_CORE_DB;
EOSQL
else
    echo "Database $LIVE_CORE_DB already exists."
fi

# Create MEDIA_DOWNLOAD_DB database if it does not exist
if ! database_exists "$MEDIA_DOWNLOAD_DB"; then
    echo "Creating $MEDIA_DOWNLOAD_DB database..."
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
        CREATE DATABASE $MEDIA_DOWNLOAD_DB;
EOSQL
else
    echo "Database $MEDIA_DOWNLOAD_DB already exists."
fi

# Create USERS_SERVICE_DB database if it does not exist
if ! database_exists "$USERS_SERVICE_DB"; then
    echo "Creating $USERS_SERVICE_DB database..."
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
        CREATE DATABASE $USERS_SERVICE_DB;
EOSQL
else
    echo "Database $USERS_SERVICE_DB already exists."
fi

# 按字母序执行 migrations 目录下的 SQL（若存在）
MIGRATIONS_DIR="/docker-entrypoint-initdb.d/migrations"
if [ -d "$MIGRATIONS_DIR" ]; then
    echo "Running SQL migrations from $MIGRATIONS_DIR ..."
    for sql_file in $(find "$MIGRATIONS_DIR" -maxdepth 1 -name '*.sql' | sort); do
        echo "Applying migration: $(basename "$sql_file")"
        psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$LIVE_CORE_DB" -f "$sql_file"
    done
fi

echo "Database initialization complete."