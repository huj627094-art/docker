"""
SEO-тесты «Подземки»: требования прошлого задания, проверяемые автоматически.

Запуск:  python manage.py test venue.tests_seo
На исходной версии сайта (до SEO-задания) почти всё будет красным — это и есть
автоматический аудит. После выполнения SEO-задания всё должно стать зелёным.
"""
import json
import re
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from django.conf import settings
from django.test import override_settings
from django.urls import reverse

from .models import Hall, Poster
from .tests import SiteTestCase

STATIC_PAGES = ["home", "hall_list", "menu", "events", "poster_list", "gallery", "contacts"]
SERVICE_PATHS = ["/booking/", "/home/", "/healthz/", "/admin/"]
HEADING = re.compile(r"^h[1-6]$")


class SeoTestCase(SiteTestCase):
    """Общие помощники: список страниц, разбор HTML."""

    def pages(self):
        """Страницы для проверки: из sitemap.xml, а если его ещё нет — из БД и маршрутов."""
        response = self.client.get("/sitemap.xml")
        if response.status_code == 200:
            locs = re.findall(r"<loc>(.*?)</loc>", response.content.decode())
            return [urlparse(loc).path for loc in locs]
        paths = [reverse(f"venue:{name}") for name in STATIC_PAGES]
        paths += [h.get_absolute_url() for h in Hall.objects.filter(is_active=True)]
        paths += [p.get_absolute_url() for p in Poster.objects.all()]
        return paths

    def soup(self, path):
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200, f"{path} отдаёт {response.status_code}")
        return BeautifulSoup(response.content, "html.parser")


class SitemapRobotsTest(SeoTestCase):
    def test_sitemap_exists(self):
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200, "Нет /sitemap.xml")
        self.assertIn("xml", response["Content-Type"])

    def test_sitemap_pages_are_200(self):
        for path in self.pages():
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_sitemap_has_active_halls_only(self):
        paths = self.pages()
        for hall in Hall.objects.all():
            with self.subTest(hall=hall.name):
                if hall.is_active:
                    self.assertIn(hall.get_absolute_url(), paths, "Активного зала нет в sitemap")
                else:
                    self.assertNotIn(hall.get_absolute_url(), paths, "Скрытый зал попал в sitemap")

    def test_sitemap_has_no_service_or_numeric_urls(self):
        paths = self.pages()
        for path in paths:
            with self.subTest(path=path):
                self.assertNotIn(path, SERVICE_PATHS, "Служебная страница в sitemap")
                self.assertIsNone(re.match(r"^/(halls|afisha)/\d+/$", path), "URL с id вместо slug")

    def test_robots_txt(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200, "Нет /robots.txt")
        self.assertTrue(response["Content-Type"].startswith("text/plain"))
        text = response.content.decode()
        self.assertRegex(text, r"(?m)^Sitemap:\s*https?://\S+/sitemap\.xml", "Нет абсолютного Sitemap:")
        self.assertRegex(text, r"(?m)^Disallow:\s*/admin/")
        self.assertRegex(text, r"(?m)^Disallow:\s*/booking/")


class MetaTagsTest(SeoTestCase):
    def test_html_lang(self):
        html = self.soup("/").find("html")
        self.assertEqual(html.get("lang"), "ru")

    def test_one_h1_on_every_page(self):
        for path in self.pages():
            with self.subTest(path=path):
                h1 = self.soup(path).find_all("h1")
                self.assertEqual(len(h1), 1, f"На странице {len(h1)} шт. <h1>")

    def test_heading_levels_not_skipped(self):
        for path in self.pages():
            with self.subTest(path=path):
                prev = 0
                for tag in self.soup(path).find_all(HEADING):
                    level = int(tag.name[1])
                    self.assertLessEqual(level, prev + 1, f"После h{prev} сразу h{level}: «{tag.get_text(strip=True)}»")
                    prev = level

    def test_titles_unique_and_length(self):
        seen = {}
        for path in self.pages():
            with self.subTest(path=path):
                title = self.soup(path).title.get_text(strip=True)
                self.assertTrue(40 <= len(title) <= 70, f"Длина title {len(title)}: «{title}»")
                self.assertNotIn(title, seen, f"Такой же title у {seen.get(title)}")
                seen[title] = path

    def test_descriptions_unique_and_length(self):
        seen = {}
        for path in self.pages():
            with self.subTest(path=path):
                tag = self.soup(path).find("meta", attrs={"name": "description"})
                self.assertIsNotNone(tag, "Нет meta description")
                text = tag.get("content", "")
                self.assertTrue(110 <= len(text) <= 170, f"Длина description {len(text)}")
                self.assertNotIn(text, seen, f"Такой же description у {seen.get(text)}")
                seen[text] = path

    def test_canonical_absolute_and_self(self):
        domain = settings.SITE_INFO["domain"]
        for path in self.pages():
            with self.subTest(path=path):
                tag = self.soup(path).find("link", rel="canonical")
                self.assertIsNotNone(tag, "Нет canonical")
                url = urlparse(tag["href"])
                self.assertIn(url.scheme, ("http", "https"), "canonical не абсолютный")
                self.assertEqual(url.netloc, domain)
                self.assertEqual(url.path, path)

    def test_og_image(self):
        for path in self.pages():
            with self.subTest(path=path):
                tag = self.soup(path).find("meta", property="og:image")
                self.assertIsNotNone(tag, "Нет og:image")
                url = tag["content"]
                self.assertRegex(url, r"^https?://", "og:image не абсолютный")
                self.assertFalse(url.lower().endswith(".svg"), "SVG соцсети не понимают")

    def test_og_image_of_hall_is_hall_photo(self):
        for hall in Hall.objects.filter(is_active=True):
            with self.subTest(hall=hall.name):
                tag = self.soup(hall.get_absolute_url()).find("meta", property="og:image")
                self.assertIsNotNone(tag)
                stem = Path(hall.image).stem  # hall-depo — имя без расширения и хэша
                self.assertIn(stem, tag["content"])

    def test_booking_is_noindex(self):
        tag = self.soup("/booking/").find("meta", attrs={"name": "robots"})
        self.assertIsNotNone(tag, "На /booking/ нет meta robots")
        self.assertIn("noindex", tag["content"])


class RedirectsAnd404Test(SeoTestCase):
    def test_home_duplicate_redirects(self):
        self.assertRedirects(self.client.get("/home/"), "/", status_code=301)

    def test_old_hall_urls_redirect_to_slug(self):
        for hall in Hall.objects.filter(is_active=True):
            with self.subTest(hall=hall.name):
                new_url = hall.get_absolute_url()
                self.assertNotRegex(new_url, r"/\d+/$", "Адрес зала всё ещё с id")
                response = self.client.get(f"/halls/{hall.pk}/")
                self.assertRedirects(response, new_url, status_code=301)

    def test_old_poster_urls_redirect_to_slug(self):
        for poster in Poster.objects.all():
            with self.subTest(poster=poster.title):
                new_url = poster.get_absolute_url()
                self.assertNotRegex(new_url, r"/\d+/$", "Адрес события всё ещё с id")
                response = self.client.get(f"/afisha/{poster.pk}/")
                self.assertRedirects(response, new_url, status_code=301)

    @override_settings(DEBUG=False)
    def test_404_page(self):
        response = self.client.get("/halls/net-takogo-zala/")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")


class ImagesAndMarkupTest(SeoTestCase):
    def test_images_have_alt_and_size(self):
        for path in self.pages():
            for img in self.soup(path).find_all("img"):
                with self.subTest(path=path, src=img.get("src")):
                    self.assertTrue(img.get("alt", "").strip(), "Пустой alt")
                    self.assertTrue(img.get("width") and img.get("height"), "Нет width/height")

    def test_json_ld(self):
        expected = {"/": {"EventVenue", "FAQPage"}, reverse("venue:hall_list"): {"BreadcrumbList"}}
        for poster in Poster.objects.all():
            expected[poster.get_absolute_url()] = {"Event", "BreadcrumbList"}
        for path, types in expected.items():
            with self.subTest(path=path):
                found = set()
                for script in self.soup(path).find_all("script", type="application/ld+json"):
                    data = json.loads(script.string)  # упадёт, если JSON невалидный
                    items = data if isinstance(data, list) else data.get("@graph", [data])
                    found |= {item.get("@type") for item in items}
                self.assertTrue(types <= found, f"Нет разметки: {types - found}")

    def test_static_images_are_light(self):
        limit = 300 * 1024
        for image in Path(settings.BASE_DIR, "static", "img").iterdir():
            with self.subTest(image=image.name):
                self.assertLessEqual(image.stat().st_size, limit, f"{image.stat().st_size // 1024} КБ")
                self.assertRegex(image.name, r"^[a-z0-9-]+\.[a-z0-9]+$", "Имя файла: латиница, цифры, дефис")
