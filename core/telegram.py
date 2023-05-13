from django.conf import settings
from django.urls import reverse
from urllib import request, parse
from kbtuopen.settings import TELEGRAM_BOT_TOKEN
import os

telegram_link = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


message_invite = """
Hi!

Login: {login}
Password: {password}

{seat}

Contest link: https://contest.kbtuopen.com
"""


def send_message(chat_id, login, password, seat):
    if seat:
        seat = "Seating: " + seat
    else:
        seat = ""

    text = message_invite.format(login=login, password=password, seat=seat)



    params = {
        'chat_id': chat_id,
        'text': text,
    }
    
    httpreq = request.Request(url=f"{telegram_link}/sendMessage?{parse.urlencode(params, doseq=True, safe='/')}", method="GET")
    

    with request.urlopen(httpreq) as httpresponse:
        status = httpresponse.status
        response = httpresponse.read().decode(
            httpresponse.headers.get_content_charset("utf-8")
        )

    return (status, response)

def get_port(request):
    if 'SERVER_PORT' in request.META:
        return request.META['SERVER_PORT']
    else:
        return None

def telegram_auth_path(request):
    url = request.build_absolute_uri(reverse('login'))
    if 'CODESPACE_NAME' in os.environ:
        codespace_name = os.getenv("CODESPACE_NAME")
        codespace_domain = os.getenv("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN")
        url = f"https://{codespace_name}-{get_port(request)}.{codespace_domain}{reverse('login')}"
    return url


def telegram_context_processor(request):
    return {
        "TELEGRAM_BOT_NAME": settings.TELEGRAM_BOT_NAME,
        "TELEGRAM_AUTH_PATH": telegram_auth_path(request),
    }