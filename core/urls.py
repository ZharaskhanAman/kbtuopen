from django.urls import path

from .views import (
    telegramLoginView,
    logoutView,
    homePageView,
    team_view,
    organization_view,
    participant_view,
    teams_view,
)

from .admin_views import export_teams_on_site, export_teams_off_site

urlpatterns = [
    path("", homePageView, name="home"),
    path("login", telegramLoginView, name="login"),
    path("logout", logoutView, name="logout"),
    path("team", team_view, name="team"),

    path("teams", teams_view, name="teams"),
    path("organization", organization_view, name="organization"),
    path("participant", participant_view, name="participant"),
]

urlpatterns += [
    path("download-accepted-teams-onsite", export_teams_on_site, name='export-teams-onsite'),
    path("download-accepted-teams-offsite", export_teams_off_site, name='export-teams-offsite'),
]
