from django.contrib import admin
from core.models import Organization, Team, Participant


@admin.action(description="Send credentials by telegram")
def send_creds(modeladmin, request, queryset):

    for team in queryset:
        team.send_credentials_by_telegram()

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('owner', 'name', 'organization', 'is_onsite', 'is_school_team', 'is_women_team', 'status', 'login', 'password', 'password_sent_at')

    list_filter = [
        "status",
        "is_onsite",
        "is_women_team",
        "is_onsite",
        "organization",
        "password_sent_at",
    ]

    actions = [send_creds]


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('team', 'full_name', 'tshirt_size',)
