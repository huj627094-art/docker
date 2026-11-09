import datetime

from django.conf import settings
from django.utils import timezone

from .models import Hall


def site_info(request):
    """Общие данные для всех шаблонов: контакты, список залов для меню и текущая акция."""
    promo = settings.PROMO
    promo_active = timezone.localdate() <= datetime.date.fromisoformat(promo["until"])
    return {
        "site": settings.SITE_INFO,
        "nav_halls": Hall.objects.filter(is_active=True),
        "promo": promo if promo_active else None,
        "umami_website_id": settings.UMAMI_WEBSITE_ID,
        "umami_script_url": settings.UMAMI_SCRIPT_URL,
    }
