from django import forms
from core.models import Team, Participant, Organization


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ('name',)


class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = ('full_name', 'tshirt_size')


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ('name', 'organization', 'is_onsite', 'is_school_team', 'is_women_team')
        labels = {
            'name': 'Team name',
        }

class CSVUploadForm(forms.Form):
    csv_file = forms.FileField()
