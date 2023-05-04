from django.conf import settings
from django.urls import reverse
from urllib import request, parse
from kbtuopen.settings import TELEGRAM_BOT_TOKEN

telegram_link = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


message_invite = """
Hi!

Login: {login}
Password: {password}

Contest link: https://contest.kbtuopen.com
"""


def send_message(chat_id, login, password):
    text = message_invite.format(login=login, password=password)

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


def telegram_context_processor(request):
    return {
        "TELEGRAM_BOT_NAME": settings.TELEGRAM_BOT_NAME,
        "TELEGRAM_AUTH_PATH": request.build_absolute_uri(reverse('login'))
    }