from itertools import groupby

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.db.models import Count
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from core.models import Room, Team
from core.seating import (
    Assignment,
    NotEnoughSeats,
    RoomSpec,
    SeatingTeam,
    count_adjacent_conflicts,
    plan_seating,
)
from core.seating_csv import parse_label
from core.strong_teams import STRONG_TEAMS, is_strong, missing_strong_teams


def eligible_teams():
    return (
        Team.objects.filter(is_onsite=True)
        .exclude(status="rejected")
        .annotate(num_members=Count("members"))
        .filter(num_members__gt=0)
        .select_related("organization")
    )


def active_rooms():
    return list(Room.objects.filter(is_active=True, capacity__gt=0))


def seating_team(team):
    return SeatingTeam(
        id=team.id,
        name=team.name,
        organization=team.organization.name,
        strong=is_strong(team.organization.name, team.name),
    )


def saved_plan(teams):
    """Assignments from the seats currently stored on teams ('Room X, seat N')."""
    return tuple(
        Assignment(team=seating_team(team), room=seat[0], position=seat[1])
        for team in teams
        for seat in [parse_label(team.seat)]
        if seat
    )


def build_plan(teams, rooms):
    seating_teams = [seating_team(team) for team in teams]
    specs = [
        RoomSpec(
            number=room.number,
            capacity=room.capacity,
            only=room.only_organization,
            lecture=room.is_lecture,
        )
        for room in rooms
    ]
    return plan_seating(seating_teams, specs)


def group_by_room(plan, teams_by_id, rooms):
    # Saved seats may point at a disabled or deleted room: still show them.
    known = {room.number: room for room in Room.objects.all()}
    room_by_number = {a.room: known.get(a.room) or Room(number=a.room, capacity=0) for a in plan}
    ordered = sorted(plan, key=lambda a: (a.room, a.position))
    return [
        {
            "room": room_by_number[number],
            "people": sum(teams_by_id[a.team.id].num_members for a in assignments),
            "arrived": sum(1 for a in assignments if teams_by_id[a.team.id].arrived_at),
            "rows": [
                {"assignment": a, "team": teams_by_id[a.team.id]}
                for a in assignments
            ],
        }
        for number, assignments in ((n, list(g)) for n, g in groupby(ordered, key=lambda a: a.room))
    ]


def dedicated_room_numbers(rooms):
    return {room.number for room in rooms if room.only_organization}


def save_plan(plan):
    updates = [Team(pk=a.team.id, seat=a.label) for a in plan]
    with transaction.atomic():
        Team.objects.bulk_update(updates, ["seat"])


def missing_strong_report(teams):
    missing = missing_strong_teams((team.organization.name, team.name) for team in teams)
    if not missing:
        return None
    names = ", ".join(f"{org}: {name}" for org, name in missing)
    return f"Из списка сильных не найдены среди рассаживаемых команд ({len(missing)} из {len(STRONG_TEAMS)}): {names}."


def distribute(request):
    """The button: seat everyone (strong teams out of lecture halls) and save."""
    teams = list(eligible_teams())
    try:
        plan = build_plan(teams, active_rooms())
    except NotEnoughSeats as error:
        messages.error(request, f"Ничего не изменено. {error}")
        return redirect("seating")
    save_plan(plan)
    messages.success(
        request, f"Рассадка сохранена: {len(plan)} команд по {len({a.room for a in plan})} кабинетам."
    )
    return redirect("seating")


@staff_member_required
@require_http_methods(["GET", "POST"])
def seating_view(request):
    if request.method == "POST":
        return distribute(request)

    preview = request.GET.get("preview") == "1"
    teams = list(eligible_teams())
    rooms = active_rooms()
    if preview:
        try:
            plan = build_plan(teams, rooms)
        except NotEnoughSeats as error:
            context = {"error": str(error), "rooms": rooms, "team_count": len(teams), "preview": True}
            return render(request, "seating.html", context)
    else:
        plan = saved_plan(teams)

    context = {
        "preview": preview,
        "groups": group_by_room(plan, {team.id: team for team in teams}, rooms),
        "rooms": rooms,
        "team_count": len(teams),
        "unseated": len(teams) - len(plan),
        "arrived_count": sum(1 for team in teams if team.arrived_at),
        "people_count": sum(team.num_members for team in teams),
        "strong_count": sum(1 for a in plan if a.team.strong),
        "missing_strong": missing_strong_report(teams),
        "capacity": sum(room.capacity for room in rooms),
        "conflicts": count_adjacent_conflicts(plan, dedicated_room_numbers(rooms)),
        "dedicated": bool(dedicated_room_numbers(rooms)),
    }
    return render(request, "seating.html", context)

    context = {
        "groups": group_by_room(plan, {team.id: team for team in teams}, rooms),
        "rooms": rooms,
        "team_count": len(teams),
        "people_count": sum(team.num_members for team in teams),
        "strong_count": sum(1 for a in plan if a.team.strong),
        "missing_strong": missing_strong_report(teams),
        "computers": sum(room.computers or 0 for room in rooms),
        "capacity": sum(room.capacity for room in rooms),
        "conflicts": count_adjacent_conflicts(plan, dedicated_room_numbers(rooms)),
        "dedicated": bool(dedicated_room_numbers(rooms)),
    }
    return render(request, "seating.html", context)
