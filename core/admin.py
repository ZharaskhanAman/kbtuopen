import logging

from django.contrib import admin
from core.models import Organization, Team, Participant
from django.http import HttpResponse

logger = logging.getLogger(__name__)


@admin.action(description="Send credentials by telegram")
def send_creds(modeladmin, request, queryset):
    for team in queryset:
        try:
            team.send_credentials_by_telegram()
        except Exception as e:
            logger.error("error occurred during sending creds to telegram %s", str(e))


@admin.action(description="Enrolls users in esep.cpfed.kz")
def enroll_teams_in_esep(modeladmin, request, queryset):
    for team in queryset:
        team.enroll_team_in_esep()


@admin.action(description="approve selected teams")
def approve_teams(modeladmin, request, queryset):
    for team in queryset:
        team.status = "accepted"

    Team.objects.bulk_update(queryset, ["status"])


@admin.action(description="reject selected teams")
def reject_teams(modeladmin, request, queryset):
    for team in queryset:
        team.status = "rejected"

    Team.objects.bulk_update(queryset, ["status"])


def export_as_codeforces_format(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/plain;charset=utf-8")

    text = ""
    for team in queryset:
        if team.members.count() > 0:
            text += team.generate_cf_format() + "\n"

    response.write(text)
    return response


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = (
        'owner',
        'name',
        'organization',
        'is_onsite',
        'is_school_team',
        'is_women_team',
        'status',
        'login',
        'password',
        'password_sent_at',
        'seat',
        'member_count',
    )

    list_filter = [
        "status",
        "is_onsite",
        "is_women_team",
        "is_onsite",
        "organization",
        "password_sent_at",
        "is_synced_with_dmoj",
    ]

    actions = [
        send_creds,
        export_as_codeforces_format,
        enroll_teams_in_esep,
        approve_teams,
        reject_teams,
    ]

    change_list_template = "team_change_list.html"

    @admin.display(description="Member count")
    def member_count(self, obj):
        return obj.members.count()


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('team', 'full_name', 'tshirt_size',)
