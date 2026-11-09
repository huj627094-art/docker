# Правила проекта «Подземка» для ИИ-агентов

Сайт банкетного зала на Django 5. Шаблоны в `templates/`, логика в `venue/`.

## Как запускать и проверять
- Локально: `python manage.py runserver` (SQLite, демо-данные уже в базе).
- В Docker: `docker compose up -d --build`, сайт на http://localhost.
- Перед тем как сказать «готово», ОБЯЗАТЕЛЬНО:
  `python manage.py test venue.tests venue.tests_seo` — всё зелёное.

## SEO-правила (нарушение = красный CI)
- На каждой странице ровно один `<h1>`, уровни заголовков без пропусков.
- Уникальные `<title>` (50–65 символов, бренд «Подземка» в конце)
  и `meta description` (120–160 символов, с призывом к действию).
- `canonical` и `og:url` — абсолютные, строятся из `site.domain`, не хардкодом.
- `og:image` — JPG/PNG 1200×630, абсолютный URL. На странице зала — фото этого зала.
- Новые страницы: добавить в `venue/sitemaps.py`; служебные — в `Disallow` и `noindex`.
- URL только ЧПУ через slug: `/halls/<slug>/`, `/afisha/<slug>/`. Старые адреса — 301.
- JSON-LD: страницы залов — `BreadcrumbList`, события — `Event`.

## Картинки
- Только в `static/img/`, имя латиницей через дефис: `hall-koltsevaya.webp`.
  Никаких пробелов, кириллицы, `IMG_1234.jpg`.
- WebP, ширина не больше 1600 px, вес до 300 КБ.
- У `<img>` всегда `alt` (что изображено, по-русски), `width`, `height`;
  ниже первого экрана — `loading="lazy"`.

## Нельзя
- Менять `docker/`, `docker-compose.yml`, `.github/` без отдельной просьбы.
- Коммитить `.env`, `db.sqlite3`, исходники фото в корень репозитория.
- Использовать `datetime.date.today()` — только `django.utils.timezone.localdate()`.
