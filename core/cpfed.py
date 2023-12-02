import json
import requests
from core.models import Team
import os


def invoke_sync_team_with_dmoj(team_id):
    team: Team = Team.objects.filter(id=team_id).first()

    login = team.login
    password = team.password
    
    url = f'https://esep.cpfed.kz/api/sync_users/{os.getenv("CPFED_TOKEN")}/'

    headers = {
        'Content-Type': 'application/json',
    }


    members  = ','.join(str(member) for member in team.members.all())

    team_name = f"{team.organization}: {team.name} - {members}"
    
    if team.is_women_team:
        team_name = "[W]" + team_name

    if team.is_school_team:
        team_name = "[S]" + team_name

    if team.is_onsite:
        org_id = 3
    else:
        org_id = 4

    data = {
        'username': login,
        'password': password,
        'full_name': team_name,
        'org_id': org_id
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    return (response.status_code, response)
