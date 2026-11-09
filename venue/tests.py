"""
Автотесты сайта. Запуск: python manage.py test

ПОДСКАЗКА: когда будете делать SEO-задания, допишите сюда свои тесты, например:
  - /robots.txt отвечает 200 и содержит строку «Sitemap:»;
  - /sitemap.xml отвечает 200 и не содержит /booking/;
  - /home/ и /halls/1/ отдают 301;
  - на каждой странице ровно один <h1>.
"""

import datetime
import io
from unittest import mock

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import BookingRequest, Hall, Poster


def aware_utc(*args):
    return datetime.datetime(*args, tzinfo=datetime.timezone.utc)


class SiteTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", stdout=io.StringIO())


class PagesTest(SiteTestCase):
    def test_static_pages_ok(self):
        for name in ["home", "hall_list", "menu", "events", "gallery", "contacts", "booking", "poster_list"]:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(f"venue:{name}")).status_code, 200)

    def test_every_hall_and_poster_page_ok(self):
        for obj in [*Hall.objects.all(), *Poster.objects.all()]:
            with self.subTest(url=obj.get_absolute_url()):
                self.assertEqual(self.client.get(obj.get_absolute_url()).status_code, 200)

    def test_inactive_hall_is_404(self):
        hall = Hall.objects.first()
        hall.is_active = False
        hall.save()
        self.assertEqual(self.client.get(hall.get_absolute_url()).status_code, 404)

    def test_admin_login_works(self):
        self.assertTrue(self.client.login(username="admin", password="podzemka2026"))


class DevOpsTest(SiteTestCase):
    def test_healthz(self):
        response = self.client.get("/healthz/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_metrics_available_for_prometheus(self):
        self.client.get("/")
        response = self.client.get("/metrics")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"django_http_requests_total_by_view_transport_method_total", response.content)

    def test_booking_goal_once(self):
        hall = Hall.objects.first()
        data = {
            "name": "Тест", "phone": "+7 (900) 000-00-00", "guests": 50, "hall": hall.pk,
            "date": (datetime.date.today() + datetime.timedelta(days=30)).isoformat(),
        }
        response = self.client.post(
            reverse("venue:booking"), data, follow=True, HTTP_REFERER="http://testserver/halls/x/",
        )
        self.assertEqual(response.context["booking_source"], "/halls/x/")
        # Обновили страницу — цель повторно не отправляется
        self.assertIsNone(self.client.get(reverse("venue:booking")).context["booking_source"])


class BookingTest(SiteTestCase):
    def form_data(self, **overrides):
        data = {
            "name": "Тест", "phone": "+7 (900) 000-00-00",
            "date": (datetime.date.today() + datetime.timedelta(days=30)).isoformat(),
            "guests": 50, "hall": Hall.objects.first().pk,
        }
        data.update(overrides)
        return data

    def test_booking_is_saved(self):
        response = self.client.post(reverse("venue:booking"), self.form_data(), follow=True)
        self.assertEqual(BookingRequest.objects.count(), 1)
        self.assertContains(response, "Заявка принята")

    def test_past_date_is_rejected(self):
        self.client.post(reverse("venue:booking"), self.form_data(date="2020-01-01"))
        self.assertEqual(BookingRequest.objects.count(), 0)

    def test_calculator_prefills_form(self):
        response = self.client.get(reverse("venue:booking"), {"guests": 120, "comment": "Расчёт с сайта"})
        self.assertContains(response, 'value="120"')
        self.assertContains(response, "Расчёт с сайта")


class PromoAndPosterTest(SiteTestCase):
    def test_promo_hidden_after_deadline(self):
        # DEVOPS: дату теперь берём через timezone.localdate(), поэтому подменяем «сейчас»
        with mock.patch("django.utils.timezone.now", return_value=aware_utc(2099, 1, 1, 12)):
            response = self.client.get(reverse("venue:home"))
        self.assertIsNone(response.context["promo"])

    @override_settings(PROMO={**settings.PROMO, "until": "2026-10-01"})
    def test_promo_deadline_by_chita_time(self):
        # DEVOPS: 1 октября 20:00 UTC — это уже 2 октября 05:00 по Чите (UTC+9).
        # Акция «до 1 октября включительно» должна быть скрыта, где бы ни стоял сервер.
        with mock.patch("django.utils.timezone.now", return_value=aware_utc(2026, 10, 1, 20)):
            response = self.client.get(reverse("venue:home"))
        self.assertIsNone(response.context["promo"])
        # А 1 октября 10:00 UTC (19:00 по Чите) — ещё показывается
        with mock.patch("django.utils.timezone.now", return_value=aware_utc(2026, 10, 1, 10)):
            response = self.client.get(reverse("venue:home"))
        self.assertIsNotNone(response.context["promo"])

    def test_past_poster_not_listed_but_regular_is(self):
        past = Poster.objects.create(
            title="Прошедшее", date=datetime.date(2020, 1, 1), short_description="-",
        )
        regular = Poster.objects.create(
            title="Регулярное", date=datetime.date(2020, 1, 1), schedule="Каждый день", short_description="-",
        )
        posters = list(self.client.get(reverse("venue:poster_list")).context["posters"])
        self.assertNotIn(past, posters)
        self.assertIn(regular, posters)
