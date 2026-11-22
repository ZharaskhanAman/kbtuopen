from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_GET, require_POST

from core.forms import CSVUploadForm
from core.models import Team
from core.seating import NotEnoughSeats, count_adjacent_conflicts
from core.seating_csv import (
    decode_upload,
    export_csv,
    parse_label,
    parse_seating_csv,
)
from core.seating_views import (
    active_rooms,
    build_plan,
    dedicated_room_numbers,
    eligible_teams,
    save_plan,
    saved_plan,
)

MAX_UPLOAD_BYTES = 1024 * 1024


def csv_response(text, filename):
    response = HttpResponse("﻿" + text, content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response["Cache-Control"] = "private, no-store, max-age=0"
    return response


@staff_member_required
@require_GET
def seating_export(request):
    teams = list(eligible_teams().prefetch_related("members").order_by("id"))
    if request.GET.get("source") == "saved":
        return csv_response(export_csv(teams, lambda team: parse_label(team.seat)), "seating_saved.csv")

    try:
        plan = build_plan(teams, active_rooms())
    except NotEnoughSeats as error:
        messages.error(request, str(error))
        return redirect("seating")
    seats = {a.team.id: (a.room, a.position) for a in plan}
    return csv_response(export_csv(teams, lambda team: seats.get(team.id)), "seating_plan.csv")


@staff_member_required
@require_POST
def seating_import(request):
    form = CSVUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        messages.error(request, "Выберите CSV-файл.")
        return redirect("seating")

    upload = form.cleaned_data["csv_file"]
    if upload.size > MAX_UPLOAD_BYTES:
        messages.error(request, "Файл слишком большой (больше 1 МБ).")
        return redirect("seating")

    teams_by_id = {team.id: team for team in Team.objects.filter(is_onsite=True).select_related("organization")}
    rooms_by_number = {room.number: room for room in active_rooms()}
    result = parse_seating_csv(decode_upload(upload.read()), teams_by_id, rooms_by_number)

    if result.errors:
        messages.error(request, "Ничего не сохранено, исправьте файл:")
        for error in result.errors:
            messages.error(request, error)
        return redirect("seating")

    save_plan(result.assignments)
    conflicts = count_adjacent_conflicts(
        saved_plan(eligible_teams()), dedicated_room_numbers(active_rooms())
    )
    messages.success(
        request,
        f"Загружено мест: {len(result.assignments)}. Сейчас соседей из одного вуза: {conflicts}.",
    )
    return redirect("seating")
