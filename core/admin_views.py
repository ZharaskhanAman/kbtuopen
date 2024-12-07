import csv
import logging

from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse

from .forms import CSVUploadForm
from .models import Team

logger = logging.getLogger(__name__)


def export_teams_on_site(request):
    if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied()
    teams = Team.objects.filter(is_onsite=True)
    return download_teams_csv(teams, 'teams_onsite.csv')


def export_teams_off_site(request):
    if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied()
    teams = Team.objects.filter(is_onsite=False)
    return download_teams_csv(teams, 'teams_off_site.csv')


def download_teams_csv(teams: QuerySet, filename):
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
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


def upload_csv(request):
    if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied()
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            decoded_file = csv_file.read().decode('utf-8-sig').splitlines()
            reader = csv.DictReader(decoded_file)
            teams_to_update = []
            for row in reader:
                try:
                    team = Team.objects.get(name=row['Login'].split('-')[1])
                    team.is_onsite = row['Is Onsite'].lower() in ['true', '1', 't']
                    team.status = row['Status']
                    team.seat = row['Seat']
                    teams_to_update.append(team)
                except Team.DoesNotExist:
                    logger.warning("team with login %s does not exist", row['Login'])
            Team.objects.bulk_update(teams_to_update, ['status', 'seat', 'is_onsite'])

            url = reverse('admin:core_team_changelist')
            return redirect(url)

    else:
        form = CSVUploadForm()

    return render(request, 'csv_upload.html', {'form': form})
