from django.urls import path

from .views import telegramLoginView, logoutView, homePageView, team_view, organization_view, participant_view, teams_view

urlpatterns = [
    path("", homePageView, name="home"),
    path("login", telegramLoginView, name="login"),
    path("logout", logoutView, name="logout"),
    path("team", team_view, name="team"),

    path("teams", teams_view, name="teams"),
    path("organization", organization_view, name="organization"),
    path("participant", participant_view, name="participant"),
]
