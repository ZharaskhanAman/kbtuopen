import hmac
from functools import wraps

from django.core.cache import cache
from django.http import Http404, JsonResponse

from core.models import ContestSettings

SESSION_KEY = "checkin_pin"
MAX_FAILED_ATTEMPTS = 10
LOCKOUT_SECONDS = 10 * 60


def configured_pin():
    return ContestSettings.load().checkin_pin.strip()


def client_ip(request):
    # Fly.io puts the real client address in this header; REMOTE_ADDR is the proxy.
    return request.META.get("HTTP_FLY_CLIENT_IP") or request.META.get("REMOTE_ADDR", "")


def _attempts_key(request):
    return f"checkin_failed:{client_ip(request)}"


def is_locked_out(request):
    return cache.get(_attempts_key(request), 0) >= MAX_FAILED_ATTEMPTS


def register_failed_attempt(request):
    key = _attempts_key(request)
    cache.add(key, 0, LOCKOUT_SECONDS)
    try:
        cache.incr(key)
    except ValueError:
        cache.set(key, 1, LOCKOUT_SECONDS)


def pin_matches(entered, pin):
    return bool(pin) and hmac.compare_digest(entered.strip().encode(), pin.encode())


def has_access(request, pin):
    if request.user.is_authenticated and request.user.is_staff:
        return True
    # Storing the pin (not a flag) means changing it in the config logs everyone out.
    return pin_matches(request.session.get(SESSION_KEY, ""), pin)


def grant_access(request, pin):
    request.session[SESSION_KEY] = pin


def require_checkin_access(view):
    """For JSON endpoints: 404 when disabled, 403 without a valid pin session."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        pin = configured_pin()
        if not pin:
            raise Http404()
        if not has_access(request, pin):
            return JsonResponse({"error": "pin_required"}, status=403)
        return view(request, *args, **kwargs)

    return wrapper
