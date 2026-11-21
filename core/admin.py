import logging

from django.contrib import admin, messages
from django.db import models
from core.models import Organization, Team, Participant, ContestSettings, Room
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse

logger = logging.getLogger(__name__)


@admin.action(description="Send credentials by telegram")
def send_creds(modeladmin, request, queryset):
    for team in queryset:
        try:
            logger.info("start sending creds for team {}".format(team.id))
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


@admin.action(description="Export for Codeforces (onsite: contest id, online: id + o)")
def export_as_codeforces_format(modeladmin, request, queryset):
    contest_id = ContestSettings.load().codeforces_contest_id.strip()
    if not contest_id:
        modeladmin.message_user(
            request, "Укажите Codeforces contest id в Contest settings.", level=messages.ERROR
        )
        return None

    teams = queryset.select_related("organization").prefetch_related("members").order_by("id")
    lines = [team.generate_cf_format(contest_id) for team in teams if team.members.all()]
    response = HttpResponse("\n".join(lines) + "\n", content_type="text/plain; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="codeforces.txt"'
    return response


class ParticipantInline(admin.TabularInline):
    model = Participant
    fields = ('full_name', 'tshirt_size')
    extra = 0


class MembersCountFilter(admin.SimpleListFilter):
    title = "members count"
    parameter_name = "members_count"

    def lookups(self, request, model_admin):
        return [
            ('0', '0 members'),
            ('1', '1 member'),
            ('2', '2 members'),
            ('3', '3 members'),
        ]

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.annotate(mc=models.Count('members')).filter(mc=int(self.value()))


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)


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
        'arrived_at',
    )

    list_filter = [
        "status",
        "is_onsite",
        "is_women_team",
        MembersCountFilter,
        "password_sent_at",
        "is_synced_with_dmoj",
        "arrived_at",
    ]

    autocomplete_fields = ['organization']

    inlines = [ParticipantInline]

    search_fields = ['name', 'organization__name', 'owner__username']

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
    search_fields = ['full_name', 'team__name']


@admin.register(ContestSettings)
class ContestSettingsAdmin(admin.ModelAdmin):
    """Singleton: the list page jumps straight to the one settings form."""

    fieldsets = (
        ("Регистрация и check-in", {"fields": ("is_registration_open", "checkin_pin")}),
        ("Логины и Codeforces", {"fields": ("login_prefix_value", "codeforces_contest_id")}),
        ("Печать и Telegram", {"fields": ("contest_url", "print_title", "print_place_date")}),
    )

    def changelist_view(self, request, extra_context=None):
        settings = ContestSettings.load()
        return redirect(reverse("admin:core_contestsettings_change", args=[settings.pk]))

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('number', 'capacity', 'computers', 'is_active', 'is_lecture', 'only_organization', 'note')
    list_editable = ('capacity', 'is_active', 'is_lecture', 'only_organization', 'note')
    list_filter = ('is_active', 'is_lecture')
