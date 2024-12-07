import csv

from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import HttpResponse
from .models import Team


def export_accepted_teams_on_site(request):
    if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied()
    teams = Team.objects.filter(status='accepted', is_onsite=True)
    return download_teams_csv(teams, 'accepted_teams_onsite.csv')


def export_accepted_teams_off_site(request):
    if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied()
    teams = Team.objects.filter(status='accepted', is_onsite=False)
    return download_teams_csv(teams, 'accepted_teams_off_site.csv')


def download_teams_csv(teams: QuerySet, filename):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.writer(response, delimiter=';')
    writer.writerow(
        [
            'Organization',
            'Login',
            'Team name',
            'Is Onsite',
            'Is school Team',
            'Is Woman team',
            'Status',
            'Seat',
            'Password sent at',
            'Members count',
            'Members',
        ]
    )
    for team in teams:
        writer.writerow(
            [
                team.organization.name,
                team.login,
                team.name,
                team.is_onsite,
                team.is_school_team,
                team.is_women_team,
                team.status,
                team.seat,
                team.password_sent_at,
                team.members.count(),
                ",".join(str(member) for member in team.members.all()),
            ]
        )
    return response
