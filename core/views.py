from django.core.exceptions import ValidationError
from django.contrib.auth import  login, get_user_model, logout
from django.shortcuts import redirect, render
from kbtuopen import settings
import hmac
import hashlib
import time
from core.models import Team
from core.forms import TeamForm, OrganizationForm, ParticipantForm
from django.db.models import Count

def logoutView(request):
    logout(request)
    return redirect('home')

def telegramLoginView(request):

    req_parameters = request.GET
    

    bot_token = settings.TELEGRAM_BOT_TOKEN

    data_check_string = ['{}={}'.format(k, v)
                             for k, v in req_parameters.items() if k != 'hash']
    
    data_check_string = '\n'.join(sorted(data_check_string))
    
    built_hash = hmac.new(hashlib.sha256(bot_token.encode()).digest(),
                        msg=data_check_string.encode(),
                        digestmod=hashlib.sha256).hexdigest()


    if built_hash != req_parameters.get('hash'):
        raise ValidationError("Invalid hash")

    current_timestamp = int(time.time())
    auth_timestamp = int(req_parameters.get('auth_date'))

    if current_timestamp - auth_timestamp > 86400:
        raise ValidationError('Auth date is outdated')
    
    user_id = req_parameters.get('id')

    User = get_user_model()

    try:
        user = User.objects.get(username=user_id)
    except User.DoesNotExist:
        user = User.objects.create(username=user_id)
        user.set_unusable_password()


    login(request, user)

    return redirect('team')





def homePageView(request):
    context = {"user": request.user}
    return render(request, "index.html", context)


def participant_view(request):
    if request.method == 'POST':
        form = ParticipantForm(request.POST)

        if form.is_valid() and request.user.team.members.count() <= 2:
            participant_form = form.save(commit = False)
            participant_form.team = request.user.team
            participant_form.save()

            return redirect('team')

    raise ValidationError("Invalid request")


def teams_view(request):
    return render(request, 'teams.html', {'teams': Team.objects.annotate(num_members=Count('members')).filter(num_members__gt=0).order_by("id")})
    
def organization_view(request): 
    if request.method == 'POST':
        form = OrganizationForm(request.POST)

        if form.is_valid():
            form.save()
        
        return redirect('team')

    elif request.method == 'GET':
        form = OrganizationForm()
    
    return render(request, 'organization.html', {'form': form})

def team_view(request):
    team = None
    form = None
    participant_form = None

    if request.method == 'POST':
        form = TeamForm(request.POST)

        if form.is_valid():
            team_form = form.save(commit = False)
            team_form.owner = request.user
            team_form.save()
        
        return redirect('team')

    elif request.method == 'GET':
       

        if request.user.is_authenticated:
            
            
            if hasattr(request.user, "team"):
                team = request.user.team
                if team.members.count() < 3:
                    participant_form = ParticipantForm()
            else:
                form = TeamForm()

             
    return render(request, 'team.html', {'form': form, 'user': request.user, 'team': team, 'participant_form': participant_form, 'is_reg_open': settings.IS_REGISTRATION_OPEN})