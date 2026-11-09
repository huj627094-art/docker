#!/bin/sh
# Подготовка перед запуском сайта. Для других команд
# (например, `docker compose run --rm web python manage.py test`) — сразу выполняем их.
set -e

if [ "$1" = "gunicorn" ]; then
    echo "→ Миграции"
    python manage.py migrate --noinput

    echo "→ Демо-данные (если база пустая; повторный запуск ничего не ломает)"
    python manage.py seed_demo

    # seed_demo создаёт учебного admin/podzemka2026 — пароль опубликован в README.
    # На сервере перезаписываем его паролем из переменной окружения.
    if [ -n "$DJANGO_ADMIN_PASSWORD" ]; then
        echo "→ Пароль администратора из DJANGO_ADMIN_PASSWORD"
        python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
u = get_user_model().objects.get(username='admin')
u.set_password(os.environ['DJANGO_ADMIN_PASSWORD'])
u.save()"
    fi

    # Метрики Prometheus от нескольких воркеров gunicorn собираются через общую папку
    export PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus
    rm -rf "$PROMETHEUS_MULTIPROC_DIR"
    mkdir -p "$PROMETHEUS_MULTIPROC_DIR"
fi

exec "$@"
