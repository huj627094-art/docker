from django.urls import path

from . import views

app_name = "venue"

urlpatterns = [
    path("", views.home, name="home"),

    # SEO-ЗАДАНИЕ (дубли страниц):
    # Главная страница доступна по двум адресам: / и /home/. Для поисковика это
    # два разных URL с одинаковым контентом — дубль.
    # ПОДСКАЗКА: варианты решения — 301-редирект (RedirectView с permanent=True)
    # или <link rel="canonical">. Что лучше в этом случае и почему?
    path("home/", views.home, name="home_duplicate"),

    path("halls/", views.hall_list, name="hall_list"),
    # SEO-ЗАДАНИЕ (ЧПУ): замените <int:pk> на <slug:slug> (см. venue/models.py)
    path("halls/<int:pk>/", views.hall_detail, name="hall_detail"),

    path("menu/", views.menu, name="menu"),
    path("events/", views.events, name="events"),
    path("afisha/", views.poster_list, name="poster_list"),
    # SEO-ЗАДАНИЕ (ЧПУ): и здесь <int:pk> → <slug:slug>
    path("afisha/<int:pk>/", views.poster_detail, name="poster_detail"),
    path("gallery/", views.gallery, name="gallery"),
    path("contacts/", views.contacts, name="contacts"),
    path("booking/", views.booking, name="booking"),
    path("healthz/", views.healthz, name="healthz"),  # DEVOPS: служебный, не для поисковиков
]
