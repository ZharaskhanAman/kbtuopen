from django.conf import settings
from django.urls import reverse
from urllib import request, parse
from kbtuopen.settings import TELEGRAM_BOT_TOKEN
from core.seating import org_tokens
from core.seating_csv import parse_label
import os

telegram_link = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


CONTEST_LINK = "http://kbtuopen26.contest.codeforces.com/"
LAPTOP_UNIVERSITIES = {"kbtu", "кбту"}

LAPTOP_NOTICE = (
    "KBTU students: please bring your own laptop.\n"
    "Студенты КБТУ: пожалуйста, возьмите с собой ноутбук."
)


def needs_laptop(organization):
    return bool(org_tokens(organization) & LAPTOP_UNIVERSITIES)


def seating_lines(seat):
    if not seat:
        return []
    parsed = parse_label(seat)
    if parsed is None:
        return [f"Seat: {seat}"]
    room, position = parsed
    return [f"Room: {room}", f"Seat: {position}"]


def build_credentials_message(login, seat, organization):
    """Message for onsite teams: login and seat. The password is intentionally
    not sent; onsite teams get it at the venue / on their team page."""
    blocks = [
        "Hi!",
        f"Login: {login}",
        "\n".join(seating_lines(seat)),
        LAPTOP_NOTICE if needs_laptop(organization) else "",
        f"Contest link: {CONTEST_LINK}",
    ]
    return "\n\n".join(block for block in blocks if block)


def build_online_message(login, password):
    """Online teams have no seat and need the password to log in remotely."""
    return "\n\n".join([
        "Hi!",
        f"Login: {login}\nPassword: {password}",
        f"Contest link: {CONTEST_LINK}",
    ])


def send_message(chat_id, text):
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