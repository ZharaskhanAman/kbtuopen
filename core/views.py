from django.core.exceptions import ValidationError
from django.contrib.auth import  login, get_user_model, logout
from django.shortcuts import redirect, render
from kbtuopen import settings
import hmac
import hashlib
import time
from core.models import Team, ContestSettings
from core.forms import TeamForm, OrganizationForm, ParticipantForm
from django.db.models import Count
from django.core.exceptions import PermissionDenied

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

    is_registration_open = ContestSettings.objects.get(id=1)         
    return render(request, 'team.html', {'form': form, 'user': request.user, 'team': team, 'participant_form': participant_form, 'is_reg_open': is_registration_open})


def delete_team(request):
    user = request.user
    if not user or not user.is_authenticated:
        raise PermissionDenied("User must be authenticated.")

    try:
        team = user.team
    except AttributeError:
        raise PermissionDenied("User has no team.")

    team.delete()
    return redirect('home')


def icpc26_results_view(request):
    teams = [
        {"rank": 1,   "name": "Master ka4ka",          "members": "Perdebay, Syrgabayev, Torekeldi",          "solved": 7, "penalty": "07:58:44"},
        {"rank": 2,   "name": "One more line",          "members": "Aspandiyarov, Beloussov, Merezhko",        "solved": 7, "penalty": "12:32:55"},
        {"rank": 4,   "name": "Min Code – Max Glow",    "members": "Abdulla, Kairat, Kaisa",                   "solved": 7, "penalty": "16:12:26"},
        {"rank": 18,  "name": "Rezero",                 "members": "Ashirbekov, Sopygali, Tobzhanov",          "solved": 6, "penalty": "07:12:46"},
        {"rank": 25,  "name": "O(DA²)",                 "members": "Darmakhan, Sergazyuly, Telengutov",        "solved": 6, "penalty": "10:00:21"},
        {"rank": 29,  "name": "Plus ULTRA",             "members": "Assalbekuly, Nurgazin, Rustem",            "solved": 6, "penalty": "11:03:21"},
        {"rank": 30,  "name": "Dzat",                   "members": "Amankulov, Amankulov, Oralbayev",          "solved": 6, "penalty": "12:33:22"},
        {"rank": 33,  "name": "IOMCHYDTCRY",            "members": "Lee, Nurikhanov, Taubay",                  "solved": 6, "penalty": "13:45:09"},
        {"rank": 37,  "name": "trust me bro",           "members": "Omarov, Yergali, Yermek",                  "solved": 6, "penalty": "14:42:28"},
        {"rank": 49,  "name": "len' dumat'",            "members": "Bekmurzin, Olzhabay, Ulykbek",             "solved": 5, "penalty": "05:21:56"},
        {"rank": 57,  "name": "pobedimye",              "members": "Bakhramov, Issayev, Talgatuly",            "solved": 5, "penalty": "07:56:34"},
        {"rank": 74,  "name": "Shadrinskoe 7.1",        "members": "Garifolla, Nursultan, Shpanova",           "solved": 5, "penalty": "16:08:46"},
        {"rank": 85,  "name": "Cicadas",                "members": "Kengesbek, Magzhan, Nogaibek",             "solved": 4, "penalty": "03:25:55"},
        {"rank": 89,  "name": "amebas",                 "members": "Imangali, Kaibulla, Sagit",                "solved": 4, "penalty": "04:30:34"},
        {"rank": 94,  "name": "KBTU 1",                 "members": "Akberen, Amanbay, Manarbek",               "solved": 4, "penalty": "06:43:20"},
        {"rank": 100, "name": "iq: below zero",         "members": "Alan, Aubakirov, Orunbai",                 "solved": 4, "penalty": "08:25:45"},
        {"rank": 104, "name": "CarTop",                 "members": "Aliyev, Kalmurat, Karbuzov",               "solved": 4, "penalty": "09:43:20"},
        {"rank": 112, "name": "SunQar",                 "members": "Akhmetov, Myktybek, Sokolovskiy",          "solved": 4, "penalty": "11:23:00"},
        {"rank": 133, "name": "unemployment",           "members": "Alimkhan, Nurislam, Nurym",                "solved": 3, "penalty": "01:46:48"},
        {"rank": 134, "name": "probably optimal",       "members": "Abdulaziz, Abishev, Murat",                "solved": 3, "penalty": "02:14:25"},
        {"rank": 137, "name": "L3GENDS",                "members": "Azim, Berdibek, Erkintaev",                "solved": 3, "penalty": "02:31:47"},
        {"rank": 139, "name": "sub 0",                  "members": "Danial, Makhmud, Nurkanat",                "solved": 3, "penalty": "02:56:59"},
        {"rank": 142, "name": "Attention is all u need","members": "Kurmanalina, Kushekbayev, Shamsadinov",    "solved": 3, "penalty": "03:17:53"},
        {"rank": 146, "name": "Arcade",                 "members": "Leonid, Temirov, Zuyev",                   "solved": 3, "penalty": "03:39:22"},
        {"rank": 154, "name": "DreamTeam",              "members": "Ospan, Sarsenov, Satayev",                 "solved": 3, "penalty": "04:39:45"},
        {"rank": 156, "name": "Doitter",                "members": "Abeuov, Sagyndyq, Taubay",                 "solved": 3, "penalty": "05:08:53"},
        {"rank": 163, "name": "VibeCoders",             "members": "Khamzin, Mukhametkali, Zhylkybay",         "solved": 3, "penalty": "06:16:12"},
        {"rank": 164, "name": "1stTab",                 "members": "Abdaly, Raiymbek, Serikbay",               "solved": 3, "penalty": "06:22:37"},
        {"rank": 167, "name": "Stack Underflow",        "members": "Baisarinov, Baktygerey, Kenenbayev",       "solved": 3, "penalty": "06:52:05"},
        {"rank": 171, "name": "The Nameless Three",     "members": "Karimov, Nursultan, Zhantore",             "solved": 3, "penalty": "08:01:48"},
        {"rank": 185, "name": "BUIYRSA",                "members": "Adilkhan, Kosshy, Orynbassar",             "solved": 3, "penalty": "13:55:28"},
        {"rank": 190, "name": "Claude Wars",            "members": "Duda, Miroslav, Shamrikov",                "solved": 2, "penalty": "00:51:31"},
        {"rank": 196, "name": "Ghosts",                 "members": "Assan, Aushet, Kyrykbay",                  "solved": 2, "penalty": "01:20:32"},
        {"rank": 202, "name": "For the Emperor",        "members": "Kamalbek, Markabaev, Timuruly",            "solved": 2, "penalty": "01:37:23"},
        {"rank": 206, "name": "Perfect Square",         "members": "Moldabayev, Orynbassar, Sabyrov",          "solved": 2, "penalty": "01:47:31"},
        {"rank": 214, "name": "O(∞)",                   "members": "Dengelov, Ilya, Ivan",                     "solved": 2, "penalty": "02:23:48"},
        {"rank": 224, "name": "Mathochists",            "members": "Bakbergen, Dochshechkina, Uteulova",       "solved": 2, "penalty": "03:08:40"},
        {"rank": 234, "name": "AIM",                    "members": "Azamatov, Kerimbay, Toktarov",             "solved": 2, "penalty": "03:48:34"},
        {"rank": 238, "name": "Runtime Terror1",        "members": "Khanbekov, Korkmazov, Zakirov",            "solved": 2, "penalty": "04:04:20"},
        {"rank": 271, "name": "O(logn)",                "members": "Gaibulla, Oralbek, Ortay",                 "solved": 2, "penalty": "09:05:33"},
        {"rank": 282, "name": "Cookers",                "members": "amanbek, Malik, Perdekozhin",              "solved": 1, "penalty": "—"},
        {"rank": 286, "name": "Infinite Loop",          "members": "Kabylbek, Rakhmatbek, Shatekova",          "solved": 1, "penalty": "—"},
        {"rank": 302, "name": "C1",                     "members": "Kireikhankyzy, Sagdiyeva, Sarzhan",        "solved": 1, "penalty": "—"},
        {"rank": 303, "name": "0 chances to win",       "members": "Beldiyar, Nesipkhan, Sanzhar",             "solved": 1, "penalty": "—"},
    ]
    return render(request, 'icpc26_results.html', {'teams': teams})
