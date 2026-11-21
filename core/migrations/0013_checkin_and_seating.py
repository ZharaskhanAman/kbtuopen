# Check-in (Team.arrived_at, ContestSettings.checkin_pin), login prefix in config,
# and seating (Room + initial rooms).

from django.db import migrations, models

# (number, note, computers, team capacity, is_lecture, only_organization) —
# from the organizers' room table; edit later in admin → Rooms.
ROOMS = [
    (2, "Жанболат", 31, 12, False, ""),
    (140, "закрыт", None, 10, False, ""),
    (161, "библиотека", None, 10, False, ""),
    (164, "библиотека", None, 18, False, ""),
    (257, "закрыт", None, 10, False, ""),
    (258, "", 25, 12, False, ""),
    (269, "", 33, 19, False, ""),
    (270, "madiyar", 29, 15, False, ""),
    (280, "", 11, 7, False, ""),
    (337, "Hudp72", 13, 7, False, ""),
    (339, "Hudp72", 12, 7, False, ""),
    (359, "закрыт", None, 0, False, ""),
    (364, "", None, 30, True, "KBTU"),
    (365, "Жанболат", 41, 21, False, ""),
    (376, "", 21, 10, False, ""),
    (377, "Frogi", 24, 12, False, ""),
    (379, "", 20, 8, False, ""),
    (438, "", 37, 19, False, ""),
    (444, "", None, 30, True, "KBTU"),
    (455, "Alikhan", 30, 18, False, ""),
]


def seed_rooms(apps, schema_editor):
    Room = apps.get_model("core", "Room")
    for number, note, computers, capacity, is_lecture, only_organization in ROOMS:
        Room.objects.update_or_create(
            number=number,
            defaults={
                "note": note,
                "computers": computers,
                "capacity": capacity,
                "is_active": capacity > 0,
                "is_lecture": is_lecture,
                "only_organization": only_organization,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_contestsettings'),
    ]

    operations = [
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.PositiveIntegerField(unique=True)),
                ('capacity', models.PositiveIntegerField(default=0, help_text='Сколько команд помещается')),
                ('computers', models.PositiveIntegerField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True, help_text='Использовать в рассадке')),
                ('note', models.CharField(blank=True, default='', max_length=100)),
                ('only_organization', models.CharField(blank=True, default='', help_text='Только для команд этого вуза (например KBTU). Пусто — для всех.', max_length=50)),
                ('is_lecture', models.BooleanField(default=False, help_text='Лекционный зал: сильные команды сюда не садятся')),
            ],
            options={
                'ordering': ['number'],
            },
        ),
        migrations.AddField(
            model_name='contestsettings',
            name='checkin_pin',
            field=models.CharField(blank=True, default='', help_text='Пин для страницы /checkin. Пустой — страница выключена.', max_length=32),
        ),
        migrations.AddField(
            model_name='contestsettings',
            name='login_prefix_value',
            field=models.CharField(default='kbtuspring26-', help_text='Логин команды = префикс + id, например kbtuspring26-123. Меняйте до рассылки логинов: уже выданные логины изменятся.', max_length=30, verbose_name='login prefix'),
        ),
        migrations.AddField(
            model_name='team',
            name='arrived_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(seed_rooms, migrations.RunPython.noop),
    ]
