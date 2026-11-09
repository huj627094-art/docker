from django.contrib import admin
from django.urls import include, path

# SEO-ЗАДАНИЕ (robots.txt):
# ПОДСКАЗКА: robots.txt должен открываться по адресу /robots.txt (строго в корне сайта).
# Самый простой способ — TemplateView с content_type="text/plain":
#
#   from django.views.generic import TemplateView
#   path("robots.txt", TemplateView.as_view(
#       template_name="robots.txt", content_type="text/plain")),
#
# Сам шаблон templates/robots.txt нужно создать. Не забудьте строку Sitemap: ...

# SEO-ЗАДАНИЕ (sitemap.xml):
# ПОДСКАЗКА:
#   from django.contrib.sitemaps.views import sitemap
#   from venue.sitemaps import StaticViewSitemap, HallSitemap
#   sitemaps = {"static": StaticViewSitemap, "halls": HallSitemap}
#   path("sitemap.xml", sitemap, {"sitemaps": sitemaps},
#        name="django.contrib.sitemaps.views.sitemap"),
# Файл venue/sitemaps.py уже лежит в проекте — там заготовка с подсказками.

urlpatterns = [
    path("admin/", admin.site.urls),
    # DEVOPS: /metrics для Prometheus. Наружу nginx этот путь не отдаёт.
    path("", include("django_prometheus.urls")),
    path("", include("venue.urls")),
]

# SEO-ЗАДАНИЕ (страница 404):
# ПОДСКАЗКА: Django сам покажет templates/404.html, если DEBUG = False.
# Создайте такой шаблон (в стиле сайта, с навигацией и ссылкой на главную).
# Проверить: запустите с DJANGO_DEBUG=0 и флагом --insecure (см. README).
