"""Настройки gunicorn для «Подземки»."""
import os

bind = "0.0.0.0:8000"
workers = int(os.environ.get("GUNICORN_WORKERS", "3"))
timeout = 30
accesslog = "-"   # логи в stdout -> `docker compose logs web`
errorlog = "-"


def child_exit(server, worker):
    # Убираем метрики завершившегося воркера, чтобы Prometheus не считал их вечно
    if os.environ.get("PROMETHEUS_MULTIPROC_DIR"):
        from prometheus_client import multiprocess
        multiprocess.mark_process_dead(worker.pid)
