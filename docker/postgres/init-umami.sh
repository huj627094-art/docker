#!/bin/sh
# Выполняется ОДИН раз — при первом создании тома с базой.
# Создаёт отдельного пользователя и базу для Umami.
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<SQL
CREATE USER umami WITH PASSWORD '$UMAMI_DB_PASSWORD';
CREATE DATABASE umami OWNER umami;
SQL
