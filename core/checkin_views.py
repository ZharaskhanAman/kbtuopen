from django.db.models import Count
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from core.checkin_access import (
    configured_pin,
    grant_access,
    has_access,
    is_locked_out,
    pin_matches,
    register_failed_attempt,
    require_checkin_access,
)
from core.models import Team


def onsite_teams():
    return (
        Team.objects.filter(is_onsite=True)
        .annotate(num_members=Count("members"))
        .filter(num_members__gt=0)
        .select_related("organization")
        .prefetch_related("members")
        .order_by("name")
    )


def render_pin_form(request, error=None, status=200):
    return render(request, "checkin_pin.html", {"error": error}, status=status)


def handle_pin_submit(request, pin):
    if is_locked_out(request):
        return render_pin_form(request, "Слишком много попыток. Подождите 10 минут.", status=429)
    if not pin_matches(request.POST.get("pin", ""), pin):
        register_failed_attempt(request)
        return render_pin_form(request, "Неверный пин")
    grant_access(request, pin)
    return redirect("checkin")


@require_http_methods(["GET", "POST"])
def checkin_view(request):
    pin = configured_pin()
    if not pin:
        raise Http404()
    if request.method == "POST":
        return handle_pin_submit(request, pin)
    if not has_access(request, pin):
        return render_pin_form(request)

    teams = list(onsite_teams())
    arrived = [team for team in teams if team.arrived_at]
    context = {
        "teams": teams,
        "arrived_count": len(arrived),
        "total_members": sum(team.num_members for team in teams),
        "arrived_members": sum(team.num_members for team in arrived),
    }
    return render(request, "checkin.html", context)


@require_POST
@require_checkin_access
def checkin_toggle(request, team_id):
    team = get_object_or_404(Team, pk=team_id, is_onsite=True)
    arrived_at = None if team.arrived_at else timezone.now()
    Team.objects.filter(pk=team.pk).update(arrived_at=arrived_at)
    return JsonResponse(
        {
            "arrived": arrived_at is not None,
            "arrived_at": arrived_at.isoformat() if arrived_at else None,
        }
    )
