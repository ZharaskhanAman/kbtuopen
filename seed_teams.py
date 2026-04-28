"""
Run with: python manage.py shell < seed_teams.py
"""
import django
from django.contrib.auth.models import User
from core.models import Organization, Team, Participant

teams_data = [
    (1, "Primaty", "MSU TASHKENT BRANCH", ["Nodir", "Nurzat", "Rajabboy"], False, False, False),
    (2, "Binary Legends", "Tashkent University of Information Technologies", ["Mamurjon Mirzapolatov", "Ozodbek Dalaboyev", "Khalimov Sarvar"], True, False, False),
    (3, "Proxima Nova", "NSPhM Almaty", ["Kassymov Nurzat"], False, False, False),
    (4, "mbi", "Tashkent University of Information Technologies", ["Maqsud Baxriddinov", "Azimjon Yusufov"], False, False, False),
    (5, "Skywalkers", "БИЛ", ["Mussin Akhmet", "Ryskul Ali"], False, True, False),
    (6, "MMM", "БИЛ", ["Мансур Мамадахунов", "Исатай Исмағзи", "Алдияр Сейтбай"], True, True, False),
    (7, "Enigma", "KBTU", ["Aidosuly Mansur", "Akbergen Yernar", "Suleimenov Madi"], True, False, False),
    (8, "Lobsters", "KBTU", ["Maxim Zuyev", "Yerden Imangali", "Valeriya Sagit"], True, False, False),
    (9, "KbtU", "KBTU", ["Bayramovich Ilyas", "Rahatuly Zhanibek"], True, False, False),
    (10, "Fichka", "NIS phmd Almaty", ["Алихан Мухаметқали"], True, True, False),
    (11, "Bullet does not ask for the address", "ADA University", ["Raul Aghayev", "İlkin Hasanov", "İbrahim Aghazada"], False, False, False),
    (12, "задача трех тел", "UNIST", ["Eldar Kusdavletov", "Adilet Abu", "Adilet Zauytkhan"], False, False, False),
    (13, "popadays", "KBTU", ["Bigeldin Nurdaulet"], True, False, False),
    (14, "Айнұр Жұмағазыева", "Айнұр Жұмағазыева", ["Ainur Zhumagazyeva"], True, False, False),
    (15, "ALT TAB", "DIDOGRAMM", ["Тәңірберген Медет", "Алтаев Еламан", "Авазхан Нұрым"], True, False, False),
    (16, "meatriders", "Атбасар НИШ", ["Adil Baibolov", "Amir Belgimbayev", "Abulmansur Khakimgali"], True, True, False),
    (17, "MANTY", "IITU", ["Нұртай Толымбек"], True, False, False),
    (18, "BRUH", "NIS CBD Almaty", ["Anuar Zhambakin", "Eskander Sadykov", "Apple"], False, True, False),
    (19, "DWPOFFD", "KBTU", ["Semey Madiyar", "Karimova Kamila"], True, False, False),
    (20, "WECAMETOTHEKBTUOPENTOEATDONER", "KBTU", ["Baishuakov Magzhan", "Nogaibek Danial", "Kambar Daulet"], True, False, False),
    (21, "Koko shmisy", "BIL + NURMAKOV", ["Zhangeldi Sanhzar Kuanishuli", "Бүркітбаев Бейбіт Сәрсенбайұлы", "Серікбай Елнұр Асхатұлы"], False, True, False),
    (22, "Туда Сюда Три донера", "KBTU", ["Ли Арсен", "Нуриханов Тимур", "Курмаш Нуржан"], True, False, False),
    (23, "МММ", "NIS Taldykorgan", ["Асхат Мансур", "Кенжебек Манас", "Аманкос Малика"], False, True, False),
    (24, "FR33Le$bianki", "Alabuga polytech", ["Farkhat Zhutanov", "Sim Khanbin", "Serikbaiuly Serzhan"], True, False, True),
    (25, "GTF", "KBTU", ["Sarsenov Yernar", "Satayev Adilet", "Ospan Ulzhan Muratkyzy"], False, False, False),
    (26, "Solomon", "Tashkent State University of Economics", ["Khursandov Kamoliddin", "Shohruh Sulaymonov", "Umar Maxmudov"], False, False, False),
    (27, "Blackpink", "KRShL54", ["Timofey Chekalenko", "Байсалбекова Гаухар Улановна", "Леонов Марк"], True, True, False),
    (28, "Babymonster", "KRShL54", ["Байсалбекова Гаухар Улановна"], True, True, True),
    (29, "Baga", "РФМШ", ["Adilkhan Meirkha", "Altair Yerimbetov", "Andrey Yudenich"], False, True, False),
    (30, "Қанағаттандырылмағандықтарыңыздан", "SDU+KBTU+ЖЕНПУ", ["Сейсен Досымжан", "Үсіпбек Темірлан", "Есберген Роза"], True, False, False),
    (31, "по рофлу залетел", "KBTU", ["Ионов Илья"], True, False, False),
    (32, "Dod-IQ", "Satbayev University + METU", ["Титов Никита", "Абишев Ратмир Мухаметгалиевич", "Темирбаев Кенесары Нурланович"], True, False, False),
    (33, "Zhateu", "РФМШ", ["Sultan Erniyaz", "Kadyrkulov Aibar", "Daulet Temirali"], True, True, False),
    (34, "Клан Учиха", "РФМШ", ["Божко Илья", "Мирманов Амир", "Еренов Ануар"], False, True, False),
    (35, "Alisherka", "IITU", ["Alisher Askarov"], False, False, False),
    (36, "AzTUman", "Azerbaijan Technical University", ["Samad Mastanov", "Alimdar Musayev", "Yusif Ismayilov"], False, False, False),
    (37, "Мопсы", "KBTU", ["Seidilda Akylbek", "Seitbek Arnur"], True, False, False),
    (38, "Eva01", "Озат", ["Ali Nurym"], True, True, False),
    (39, "UNEC Zaqatala", "UNEC Zaqatala", ["Səlim Zaid Bəhruz", "Mamedov Murad Ağacan", "Sultanov Məhəmməd Pərviz"], False, False, False),
    (40, "Team falcons", "СШЛ 178", ["Қуаныш Мейірлан"], False, True, False),
    (41, "Закодированные", "Sl 165 + NIS", ["Maulet Aibar Aidynulu", "Qudaibergen Yerassyl"], True, True, False),
    (42, "Супергерои Х", "РФМШ", ["Даурен Мирас", "Жан Анри", "Сламжан Ералим"], True, True, False),
    (43, "В топе без Айбара", "NU + Vertex + Wildberries", ["Adlet Dautbek", "Roman Chesnokov", "Abay Baimukanov"], True, False, False),
    (44, "Polykek", "Satbayev University", ["Demid Metelnikov", "Raimbek Baizakov", "Malika Andas"], True, False, False),
    (45, "SunQar", "KBTU", ["Myktybek Aksungkar", "Ivan Sokolovskii", "Akhmetov Abilmansur"], True, False, False),
    (46, "Escalade", "KBTU", ["Assalbekuly Almaz", "Nurgazin Nurassyl", "Rustem Arsen"], True, False, False),
    (47, "Little fires everywhere", "NARXOZ+SDU+UNIST", ["Dauren Maskeugaliyev", "Ibrahim Serkebay", "Ildar Kanaliyev"], True, False, False),
    (48, "JAS Alliance", "SDU + KBTU", ["Shadiyar Kholmerzayev", "Nursoltan Adilet", "Kamal Zhanserik"], True, False, False),
    (49, "Lowtier trashes", "РФМШ+173 лицей", ["Жанат Ернур", "Батырхан Аликерим", "Корганбаев Жангир"], True, True, False),
    (50, "For fun", "KBTU", ["Yergazy Adil Daurenuly"], True, False, False),
    (51, "lol_xd", "IITU", ["Li Denis", "Turebekov Dias", "Bekmuhan Talgat"], False, False, False),
    (52, "nanocats", "unnamed organization", ["Yermek Nurbakhyt", "Ulbossyn Bakbergenkyzy", "Sungyla Zhunisbekkyzy"], True, False, False),
    (53, "Beefsteak", "NIS Almaty Medeu", ["Ayaulym Yussupova", "Nurakhan Aibike"], True, True, True),
    (54, "Сахарку бы", "KBTU + IITU", ["Shermukhamedov Timur", "Konratov Sagyntay"], True, False, False),
    (55, "Sclerosis patients", "KBTU", ["Zhanazarov Iskander", "Khamzin Abay"], True, False, False),
    (56, "Bombariki", "MOU Sapat", ["Nurislam Karypzhanov", "Adilkhan Kadyrov", "Dosaliev Aman"], False, True, False),
    (57, "Solo", "БИЛ", ["Abugaliyev Zhangirkhan"], False, True, False),
    (58, "shiratorizawa", "SDU", ["Andrei Kuzmin", "Dauren Baimurza", "Yerzhan Amangeldin"], True, False, False),
    (59, "GRWM", "РФМШ", ["Olzhas Myrzakhmet", "Armanzhan Alikhan", "Rustam Dimash"], True, True, False),
    (60, "Aksay tigers", "Aksay BIL", ["Сабыр Тансыкбай", "Маулет Арнур", "Асетулы Али Амир"], True, True, False),
    (61, "MMA", "IITU + NISPhM", ["Orazbaev Madi", "Targyn Manas", "Satbayev Aman"], True, False, False),
    (62, "Hugh jazz men", "Bbl", ["Boiko Konstantin Yuryevich", "Gomarteli David Givievich", "Guro Alexander Alexandrovich"], True, False, False),
    (63, "GAN", "KBTU", ["Nurkhan Zhamalbekov", "Gulsezim Mukhanbetkul"], True, False, False),
    (64, "B3", "KBTU", ["Galym Orunby", "Aksynkar"], True, False, False),
    (65, "mmmda", "KBTU", ["Orynbassar Nurali", "Khalel Muslim", "Torekhan Danial"], True, False, False),
    (66, "№16_pater", "KBTU", ["Bakbergen Shyngys", "Baitaliev Dinmuhamed", "Kosherbayev Abilseiit"], True, False, False),
    (67, "CodeAny", "ADA University", ["Huseyn Hajiyev"], False, False, False),
    (68, "f3", "KBTU", ["Kenzhegaliyev Nursultan", "Orunbay Batyrzhan", "Yerlepes Bek"], True, False, False),
    (69, "Viltrum", "Satbayev University", ["Yedil Abdresh", "Yerkebulan Qaldybek", "Ayan Shaimurat"], True, False, False),
    (70, "Error 404", "KBTU", ["Temirov Eldar", "Yernur Tazhibaev"], True, False, False),
    (71, "хмурый 5б", "РФМШ", ["Церковный Илья", "Токтасын Иманали", "Тулепбергенов Арсен"], True, True, False),
    (72, "TriBak", "Khazar University", ["Nihad Masmaliyev", "Anar Nurayev", "Ulvi İlyasov"], False, False, False),
    (73, "Triple T", "Sl 165", ["Карлыбаев Мирас", "Шиповский Егор", "Оспанов Даулет"], True, True, False),
    (74, "AlMaTi", "Semey BIL", ["Ali Mendeke", "Magzhan Dastanuly", "Temirlan Zhunussov"], True, True, False),
    (75, "Quantum students", "РФМШ", ["Maksut Mansur", "Naratau Temirkhan", "Zheken Batyr"], False, True, False),
    (76, "570 tenge", "KBTU", ["Abylay Dalabay", "Nugman Bogenbayev", "Arslan Daminov"], True, False, False),
    (77, "ЕБА", "CS2", ["Andrey Kim", "Birzhan Auganov", "Yerzhan Auganov"], True, False, False),
    (78, "AlgaKazakhstan", "AlgaKazakhstan", ["Damirkyzy Sulamif"], False, False, True),
    (79, "Hamza's team", "SDU", ["Karymsakov Almat", "Hamza Shagdar", "Alikhan Abdikulov"], True, False, False),
    (80, "Pablo", "KBTU", ["Abishev Kadirzhan"], True, False, False),
    (81, "AIMachievers", "KBTU", ["Omarbekova Marzhan Askarkyzy", "Rabchenyuk Alina Olegovna"], True, False, True),
    (82, "да мы", "NU", ["Amina Baizak", "Dayana Iskhakova"], True, False, True),
    (83, "steezy", "IITU", ["Aisha Mels"], True, False, False),
    (84, "Pustye", "KBTU", ["Perdebaev Bekarys"], True, False, False),
    (85, "DoDo Pizza", "SDU", ["Abdrakhman Zhasulan", "Serikbekov Damir"], True, False, False),
    (86, "Nur_City_Team", "IITU", ["Talgat Batyrzhan", "Aydarbekov Mansur", "Nyshanbek Asylnur"], True, False, False),
    (87, "Vibe coders", "KBTU", ["Merey Polatkhan", "Tileukhan Alibay", "Zhanserik Kalmukhambet"], True, False, False),
    (88, "шадринское 7,1%", "KBTU", ["Yerbatyr Nursultan", "Mukhammed Garifolla", "Madina Shpanova"], True, False, False),
    (89, "Арбуз с майонезом", "KBTU", ["Bazargaliyev Zhandos", "Anuarbekuly Amanbek", "Norsultanov Arman"], True, False, False),
    (90, "Я переродился торговым автоматом в другом мире", "KBTU", ["Nurlybekuly Nurbekzat", "Torgoviy Automat", "Sauda Automaty"], True, False, False),
    (91, "Vozduhani228", "NIS Almaty-Medeo (фмн)", ["Maratuly Yearly", "Yerkin Daryn", "Hamidulla Dair"], False, True, False),
    (92, "Мирас,Аллияр и Святослав", "РФМШ", ["Мусин Мирас", "Димеев Святосла", "Ерболат Алдияр"], True, True, False),
    (93, "Mixture of Experts", "NARXOZ + KBTU", ["Arman Zhalgasbayev", "Makhambet Aldabergenov"], True, False, False),
    (94, "Точка с запятой", "РФМШ", ["Артур Данишевский", "Елеубек Темірәлі", "Болатұлы Мансур"], True, True, False),
    (95, "Alty", "Coventry University", ["Altyn Aldamzharova"], False, False, True),
    (96, "Cool Guys 2026", "Авторская школа Жании Аубакировой", ["Zhetkizgen Tomiris", "Jumabekova Alina Alibekovna", "Martynenko Alexandra Yurievna"], True, True, True),
]

created = 0
skipped = 0

for idx, name, org_name, members, is_onsite, is_school, is_women in teams_data:
    if Team.objects.filter(name=name).exists():
        skipped += 1
        continue

    org, _ = Organization.objects.get_or_create(name=org_name)

    username = f"seed_team_{idx}"
    user, _ = User.objects.get_or_create(username=username)

    team = Team.objects.create(
        owner=user,
        name=name,
        organization=org,
        is_onsite=is_onsite,
        is_school_team=is_school,
        is_women_team=is_women,
        status="pending",
    )

    for member_name in members:
        Participant.objects.create(team=team, full_name=member_name)

    created += 1

print(f"Done — created {created} teams, skipped {skipped} existing.")
