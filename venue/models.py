from django.db import models
from django.urls import reverse


class Hall(models.Model):
    """Зал (в стилистике сайта — «станция»)."""

    name = models.CharField("Название", max_length=100)
    slug = models.SlugField("URL", max_length=120, unique=True, null=True, blank=True)
    # SEO-ЗАДАНИЕ (ЧПУ — человекопонятные URL):
    # Сейчас залы открываются по адресу /halls/1/, /halls/2/ ... — это плохо для SEO.
    # ПОДСКАЗКА: добавьте поле
    #     slug = models.SlugField("URL", max_length=120, unique=True)
    # затем: makemigrations -> migrate, заполните slug в админке (или через
    # prepopulated_fields в admin.py), поменяйте маршрут в venue/urls.py на <slug:slug>
    # и get_absolute_url() ниже. Хорошие адреса: /halls/depo/, /halls/tonnel/
    # Будьте внимательны: unique=True на заполненной таблице требует миграции в 2 шага
    # (или временно null=True / default) — разберитесь, как это сделать.

    line_color = models.CharField(
        "Цвет линии (HEX)", max_length=7, default="#e4312b",
        help_text="Цвет «ветки метро» для зала, например #e4312b",
    )
    line_number = models.PositiveSmallIntegerField("Номер линии", default=1)
    short_description = models.CharField("Короткое описание", max_length=255)
    description = models.TextField("Полное описание")
    capacity_banquet = models.PositiveIntegerField("Вместимость (банкет)")
    capacity_buffet = models.PositiveIntegerField("Вместимость (фуршет)")
    area = models.PositiveIntegerField("Площадь, м²")
    price_from = models.PositiveIntegerField("Цена от, ₽/гость")
    features = models.TextField(
        "Особенности", blank=True,
        help_text="Каждая особенность — с новой строки",
    )
    image = models.CharField(
        "Картинка (путь в static)", max_length=200, default="img/hall-depo.jpg",
    )

    # SEO-ЗАДАНИЕ (управляемые мета-теги):
    # ПОДСКАЗКА: хорошая практика — дать контент-менеджеру возможность задать
    # title и description для каждой страницы вручную:
    #     meta_title = models.CharField(max_length=70, blank=True)
    #     meta_description = models.CharField(max_length=160, blank=True)
    # а в шаблоне выводить их, если заполнены, иначе — сгенерированные.

    order = models.PositiveSmallIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Показывать на сайте", default=True)

    class Meta:
        verbose_name = "Зал"
        verbose_name_plural = "Залы"
        ordering = ["order", "id"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("venue:hall_detail", kwargs={"slug": self.slug})

    def features_list(self):
        return [f.strip() for f in self.features.splitlines() if f.strip()]


class EventFormat(models.Model):
    """Формат мероприятия: свадьба, корпоратив, день рождения..."""

    title = models.CharField("Название", max_length=100)
    icon = models.CharField("Иконка (эмодзи или символ)", max_length=8, default="◆")
    description = models.TextField("Описание")
    order = models.PositiveSmallIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Формат мероприятия"
        verbose_name_plural = "Форматы мероприятий"
        ordering = ["order", "id"]

    def __str__(self):
        return self.title


class MenuPackage(models.Model):
    """Банкетный пакет / сет меню."""

    name = models.CharField("Название", max_length=100)
    description = models.CharField("Описание", max_length=255)
    price_per_person = models.PositiveIntegerField("Цена, ₽/гость")
    items = models.TextField("Состав", help_text="Каждая позиция — с новой строки")
    is_featured = models.BooleanField("Хит", default=False)
    order = models.PositiveSmallIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Банкетное меню"
        verbose_name_plural = "Банкетные меню"
        ordering = ["order", "id"]

    def __str__(self):
        return self.name

    def items_list(self):
        return [i.strip() for i in self.items.splitlines() if i.strip()]


class Review(models.Model):
    author = models.CharField("Имя", max_length=100)
    event = models.CharField("Мероприятие", max_length=100, blank=True)
    text = models.TextField("Текст отзыва")
    rating = models.PositiveSmallIntegerField("Оценка (1-5)", default=5)
    created_at = models.DateField("Дата")
    is_published = models.BooleanField("Опубликован", default=True)

    # ПОДСКАЗКА: отзывы с оценками — отличный повод для микроразметки
    # Schema.org AggregateRating / Review (звёздочки в сниппете).

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.author} — {self.rating}★"


class FAQ(models.Model):
    question = models.CharField("Вопрос", max_length=255)
    answer = models.TextField("Ответ")
    order = models.PositiveSmallIntegerField("Порядок", default=0)

    # ПОДСКАЗКА: вопросы-ответы можно разметить через Schema.org FAQPage (JSON-LD).

    class Meta:
        verbose_name = "Вопрос-ответ"
        verbose_name_plural = "Вопросы и ответы"
        ordering = ["order", "id"]

    def __str__(self):
        return self.question


class BookingRequest(models.Model):
    """Заявка на бронирование, оставленная через форму на сайте."""

    STATUS_CHOICES = [
        ("new", "Новая"),
        ("in_work", "В работе"),
        ("done", "Подтверждена"),
        ("cancel", "Отменена"),
    ]

    name = models.CharField("Имя", max_length=100)
    phone = models.CharField("Телефон", max_length=30)
    date = models.DateField("Дата мероприятия")
    guests = models.PositiveIntegerField("Количество гостей")
    hall = models.ForeignKey(
        Hall, verbose_name="Зал", on_delete=models.SET_NULL, null=True, blank=True,
    )
    event_format = models.ForeignKey(
        EventFormat, verbose_name="Формат", on_delete=models.SET_NULL, null=True, blank=True,
    )
    comment = models.TextField("Комментарий", blank=True)
    status = models.CharField("Статус", max_length=10, choices=STATUS_CHOICES, default="new")
    created_at = models.DateTimeField("Создана", auto_now_add=True)

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name}, {self.date:%d.%m.%Y}, {self.guests} гостей"


class Poster(models.Model):
    """Событие в афише: квиз, концерт, вечеринка — с конкретной датой."""

    title = models.CharField("Название", max_length=150)
    slug = models.SlugField("URL", max_length=120, unique=True, null=True, blank=True)
    topic = models.CharField("Тема", max_length=150, blank=True)
    organizer = models.CharField("Организатор", max_length=150, blank=True)
    date = models.DateField("Дата", help_text="Для регулярного события — дата первого проведения")
    time = models.TimeField("Время начала", null=True, blank=True)
    schedule = models.CharField(
        "Регулярность", max_length=100, blank=True,
        help_text="Например «Каждое утро». Если заполнено, событие не пропадает из афиши после даты.",
    )
    short_description = models.CharField("Короткое описание", max_length=255)
    description = models.TextField("Описание", blank=True)
    image = models.CharField("Картинка (путь в static)", max_length=200, blank=True)
    is_published = models.BooleanField("Опубликовано", default=True)

    # SEO-ЗАДАНИЕ (ЧПУ): как и у залов, адрес события сейчас /afisha/1/.
    # Хороший адрес: /afisha/kviz-60-sekund-kompyuternye-igry/ — добавьте slug.
    # ПОДСКАЗКА: у события в афише есть всё для Schema.org Event:
    # name, startDate, location (Place + PostalAddress), image, organizer, description.
    # Такая разметка может дать расширенный сниппет с датой в выдаче.
    # Для регулярных событий (schedule) в Schema.org есть eventSchedule (тип Schedule).

    class Meta:
        verbose_name = "Событие афиши"
        verbose_name_plural = "Афиша"
        ordering = ["date", "time"]

    def __str__(self):
        return f"{self.title} ({self.date:%d.%m.%Y})"

    def get_absolute_url(self):
        return reverse("venue:poster_detail", kwargs={"slug": self.slug})
