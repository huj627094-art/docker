"""
Настройки проекта «Подземка» — банкетный зал в стиле лофт / андеграунд.

Учебный проект по SEO. Ищите по проекту комментарии с пометкой «SEO-ЗАДАНИЕ»
и «ПОДСКАЗКА» — это места, которые вам предстоит доработать (см. README.md).
"""

import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# Для учебного проекта ключ по умолчанию — ок. В бою — только из переменной окружения!
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "dev-only-podzemka-secret-key-change-me-in-production-0123456789",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

# DEVOPS: на сервере (DEBUG=False) ключ из кода использовать нельзя — падаем сразу.
if not DEBUG and SECRET_KEY.startswith("dev-only"):
    raise ImproperlyConfigured("Задайте DJANGO_SECRET_KEY в переменных окружения")


def env_list(name, default=""):
    """Читает список из переменной окружения: "a,b,c" -> ["a", "b", "c"]."""
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


# DEVOPS: никаких "*" — только явно разрешённые хосты.
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost")
# Нужен, когда сайт открывают по домену/порту за nginx: иначе форма брони отдаст 403 (CSRF).
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")
# nginx сообщает Django, что исходный запрос был по HTTPS.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


INSTALLED_APPS = [
    "django_prometheus",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # SEO-ЗАДАНИЕ (карта сайта):
    # ПОДСКАЗКА: для генерации sitemap.xml в Django есть встроенный фреймворк.
    # Нужно добавить сюда "django.contrib.sitemaps" (а при желании ещё
    # "django.contrib.sites" + SITE_ID = 1, чтобы домен брался из БД).
    "venue",
]

MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",  # DEVOPS: строго первым
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # ПОДСКАЗКА (задание со звёздочкой): для 301-редиректов со старых URL
    # можно подключить "django.contrib.redirects.middleware.RedirectFallbackMiddleware"
    # (плюс приложения django.contrib.sites и django.contrib.redirects).
    "django_prometheus.middleware.PrometheusAfterMiddleware",  # DEVOPS: строго последним
]

ROOT_URLCONF = "podzemka.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "venue.context_processors.site_info",
            ],
        },
    },
]

WSGI_APPLICATION = "podzemka.wsgi.application"


# DEVOPS: есть DATABASE_URL (в Docker) — PostgreSQL, нет — SQLite, как раньше.
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=60,
    )
}


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Asia/Chita"
USE_I18N = True
USE_TZ = True


STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# DEVOPS: хэши в именах статики (style.css -> style.3f2a1c9b0d4e.css), чтобы кэшировать на год.
# Включается только в Docker (там при сборке выполнен collectstatic), локальный runserver
# и тесты по README работают как раньше.
if os.environ.get("DJANGO_STATIC_MANIFEST") == "1":
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"},
    }

# DEVOPS: self-hosted аналитика Umami. Пусто — скрипт не выводится (локально не считаемся).
UMAMI_WEBSITE_ID = os.environ.get("UMAMI_WEBSITE_ID", "")
UMAMI_SCRIPT_URL = os.environ.get("UMAMI_SCRIPT_URL", "http://localhost:3000/script.js")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Данные о заведении — доступны во всех шаблонах как {{ site.name }}, {{ site.phone }} и т.д.
# ПОДСКАЗКА: эти же данные пригодятся для микроразметки Schema.org (LocalBusiness / EventVenue)
# и для Open Graph (og:site_name).
SITE_INFO = {
    "name": "Подземка",
    "tagline": "Банкетный зал в стиле лофт и андеграунд",
    # ПОДСКАЗКА: юр. лицо — это legalName в микроразметке Organization / LocalBusiness
    "legal_name": "ИП Анисимов Игорь Владимирович",
    "domain": os.environ.get("SITE_DOMAIN", "podzemka.example"),  # SEO-ЗАДАНИЕ: пригодится для абсолютных URL (canonical, og:url)
    "phone": "+7 (900) 123-45-67",
    "phone_raw": "+79001234567",
    "email": "hello@podzemka.example",
    "address": "улица Курнатовского, 17, Чита, Забайкальский край, 672027",
    "street": "улица Курнатовского, 17",
    "city": "Чита",
    "region": "Забайкальский край",
    "country": "RU",
    "postal_code": "672027",
    "hours": "Ежедневно, 12:00 — 02:00",
    # Секретная фраза для бара: назвать бармену и получить скидку
    "bar_secret": "Дайте ходу",
    "bar_discount": 14,
    # Координаты строками: так они не превратятся в «52,03553» из-за русской локали
    "geo": {"lat": "52.035530", "lon": "113.493054"},
    "map_url": "https://yandex.ru/maps/?pt=113.493054,52.035530&z=17&l=map",
    "telegram": "https://t.me/podzemka_example",
    "vk": "https://vk.com/podzemka_example",
}

# Акция: выпускной + скидка на тамаду. Блок сам исчезает с сайта после даты окончания
# (проверка в venue/context_processors.py).
# ПОДСКАЗКА: акцию можно разметить через Schema.org Offer с полем validThrough.
PROMO = {
    "title": "Выпускной в Подземке",
    "discount": 30,
    "host_name": "Гай Манукян",
    "host_photo": "img/tamada-gai-manukyan.jpg",
    "until": "2026-10-01",       # последний день акции (включительно), формат ГГГГ-ММ-ДД
    "until_human": "1 октября",
}
