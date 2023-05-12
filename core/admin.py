from django.contrib import admin
from core.models import Organization, Team, Participant
from django.http import HttpResponse

@admin.action(description="Send credentials by telegram")
def send_creds(modeladmin, request, queryset):

    for team in queryset:
        team.send_credentials_by_telegram()


def export_as_codeforces_format(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/plain;charset=utf-8")

    text = ""
    for team in queryset:
        text += team.generate_cf_format() + "\n"

    response.write(text)
    return response


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('owner', 'name', 'organization', 'is_onsite', 'is_school_team', 'is_women_team', 'status', 'login', 'password', 'password_sent_at', 'member_count')

    list_filter = [
        "status",
        "is_onsite",
        "is_women_team",
        "is_onsite",
        "organization",
        "password_sent_at",
    ]

    actions = [send_creds, export_as_codeforces_format]

    @admin.display(description="Member count")
    def member_count(self, obj):
        return obj.members.count()


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('team', 'full_name', 'tshirt_size',)
