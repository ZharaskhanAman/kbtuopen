from django.conf import settings
from django.urls import reverse


def telegram_context_processor(request):
    return {
        "TELEGRAM_BOT_NAME": settings.TELEGRAM_BOT_NAME,
        "TELEGRAM_AUTH_PATH": request.build_absolute_uri(reverse('login'))
    }