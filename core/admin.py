from django.contrib import admin
from core.models import Organization, Team, Participant

# Register your models here.

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('owner', 'name', 'organization', 'is_onsite', 'is_school_team', 'is_women_team', 'status', )


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('team', 'full_name', 'tshirt_size',)
