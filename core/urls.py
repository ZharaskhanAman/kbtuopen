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
]

urlpatterns += [
    path("export-teams-onsite", export_teams_on_site, name='export-teams-onsite'),
    path("export-teams-offsite", export_teams_off_site, name='export-teams-offsite'),
    path("upload-csv", upload_csv, name='upload-csv'),
]
