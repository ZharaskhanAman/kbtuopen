from django.urls import path

from .views import (
    telegramLoginView,
    logoutView,
    homePageView,
    team_view,
    organization_view,
    participant_view,
    teams_view,
    delete_team,
    delete_member,
    dev_login_view,
    icpc26_results_view,
    halloffame_view,
    archive_standings_view,
    contest_view,
)

from .admin_views import export_teams_on_site, export_teams_off_site, upload_csv

urlpatterns = [
    path("", homePageView, name="home"),
    path("login", telegramLoginView, name="login"),
    path("logout", logoutView, name="logout"),
    path("team", team_view, name="team"),

    path("teams", teams_view, name="teams"),
    path("organization", organization_view, name="organization"),
    path("participant", participant_view, name="participant"),
    path('delete_team', delete_team, name='delete_team'),
    path('delete_member/<int:member_id>', delete_member, name='delete_member'),
    path('dev-login', dev_login_view, name='dev_login'),
    path('icpc26-results', icpc26_results_view, name='icpc26-results'),
    path('hall-of-fame', halloffame_view, name='halloffame'),
    path('archive', archive_standings_view, name='archive'),
    path('contest', contest_view, name='contest'),
]

urlpatterns += [
    path("export-teams-onsite", export_teams_on_site, name='export-teams-onsite'),
    path("export-teams-offsite", export_teams_off_site, name='export-teams-offsite'),
    path("upload-csv", upload_csv, name='upload-csv'),
]
