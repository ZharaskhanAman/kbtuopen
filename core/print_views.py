from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.views.decorators.http import require_GET

from core.models import ContestSettings
from core.print_pdfs import PrintTexts, Slip, TeamCard, password_slips_pdf, team_cards_pdf
from core.seating_csv import parse_label
from core.seating_views import eligible_teams


def print_texts():
    settings = ContestSettings.load()
    return PrintTexts(
        title=settings.print_title,
        place_date=settings.print_place_date,
        contest_url=settings.contest_url,
    )


def teams_in_seat_order():
    """Eligible onsite teams with their parsed seat, by room and seat; unseated last."""
    teams = eligible_teams().prefetch_related("members")
    seated = [(team, parse_label(team.seat) or (None, None)) for team in teams]
    return sorted(seated, key=lambda item: (item[1][0] is None, item[1][0] or 0, item[1][1] or 0, item[0].name.lower()))


def pdf_response(content, filename):
    response = HttpResponse(content, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@staff_member_required
@require_GET
def print_passwords(request):
    slips = [
        Slip(team.name, team.organization.name, team.login, team.password, room, seat)
        for team, (room, seat) in teams_in_seat_order()
    ]
    return pdf_response(password_slips_pdf(slips, print_texts()), "passwords.pdf")


@staff_member_required
@require_GET
def print_team_cards(request):
    cards = [
        TeamCard(team.name, team.organization.name, [m.full_name for m in team.members.all()], room, seat)
        for team, (room, seat) in teams_in_seat_order()
    ]
    return pdf_response(team_cards_pdf(cards, print_texts()), "team_cards.pdf")
