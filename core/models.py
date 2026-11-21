from django.db import models
from django.contrib.auth.models import User
from .codeforces import clean_team_name, online_contest_id
from .telegram import build_credentials_message, build_online_message, send_message
from django.core.cache import cache
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class Organization(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


STATUS = [
    ("pending", "pending"),
    ("accepted", "accepted"),
    ("rejected", "rejected"),
]

TSHIRT_SIZE = [
    ("XS", "XS"),
    ("S", "S"),
    ("M", "M"),
    ("L", "L"),
    ("XL", "XL"),
    ("XXL", "XXL"),
]


DEFAULT_LOGIN_PREFIX = "kbtuspring26-"
LOGIN_PREFIX_CACHE_KEY = "contest_settings:login_prefix"
LOGIN_PREFIX_CACHE_SECONDS = 60


def generate_random_pass():
    return User.objects.make_random_password(
        length=10,
    )


class Team(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name="team")
    name = models.CharField(max_length=50)
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)
    is_onsite = models.BooleanField()
    is_school_team = models.BooleanField()
    is_women_team = models.BooleanField()
    status = models.CharField(choices=STATUS, max_length=20, default="pending")
    password = models.CharField(max_length=10, default=generate_random_pass)
    password_sent_at = models.DateTimeField(null=True, blank=True)
    seat = models.CharField(max_length=100, blank=True, null=True)
    is_synced_with_dmoj = models.BooleanField(default=False)
    arrived_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

    @property
    def login(self):
        return f"{ContestSettings.login_prefix()}{self.id}"

    def generate_cf_format(self, contest_id):
        """Onsite teams go to contest_id, online teams to contest_id + 'o'."""
        members = ",".join(str(member) for member in self.members.all())
        name = clean_team_name(self.name, fallback=f"Team {self.id}")
        if self.is_women_team:
            name += "[W]"
        if self.is_school_team:
            name += "[S]"
        team_name = clean_team_name(f"{self.organization}: {name} - {members}")
        contest = contest_id if self.is_onsite else online_contest_id(contest_id)
        return f"{contest}| {self.login} | {self.password} | {team_name}"

    def send_credentials_by_telegram(self):
        text = (
            build_credentials_message(self.login, self.seat, self.organization.name)
            if self.is_onsite
            else build_online_message(self.login, self.password)
        )
        (status, response) = send_message(self.owner.username, text)

        if 200 <= status < 300:
            self.password_sent_at = timezone.now()
            self.save()
        else:
            logger.info(
                f"Failed to sent credentials to team {self.name} owner {self.owner.username}"
            )
            logger.info(f"Response: {response}")

    def enroll_team_in_esep(self):
        if self.is_synced_with_dmoj:
            logger.info(f"Already enrolled! Skipping team {self.name}")
            return

        from core.cpfed import invoke_sync_team_with_dmoj
        (status, response) = invoke_sync_team_with_dmoj(self.id)

        if 200 <= status < 300:
            self.is_synced_with_dmoj = True
            self.save()
        else:
            logger.info(
                f"Failed to sent credentials to team {self.name} owner {self.owner.username}"
            )
            logger.info(f"Response: {response}")


class Participant(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="members")
    full_name = models.CharField(max_length=50)
    tshirt_size = models.CharField(choices=TSHIRT_SIZE, max_length=5, default="M")

    def __str__(self):
        return self.full_name


class ContestSettings(models.Model):
    is_registration_open = models.BooleanField(default=True)
    checkin_pin = models.CharField(
        max_length=32,
        blank=True,
        default="",
        help_text="Пин для страницы /checkin. Пустой — страница выключена.",
    )

    login_prefix_value = models.CharField(
        "login prefix",
        max_length=30,
        default=DEFAULT_LOGIN_PREFIX,
        help_text="Логин команды = префикс + id, например kbtuspring26-123. "
        "Меняйте до рассылки логинов: уже выданные логины изменятся.",
    )

    codeforces_contest_id = models.CharField(
        "Codeforces contest id",
        max_length=20,
        blank=True,
        default="",
        help_text="Для экспорта в Codeforces: оффлайн-команды получают этот id, онлайн — id + «o».",
    )

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete(LOGIN_PREFIX_CACHE_KEY)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @classmethod
    def login_prefix(cls):
        """Cached: Team.login is rendered for hundreds of teams per page."""
        prefix = cache.get(LOGIN_PREFIX_CACHE_KEY)
        if prefix is None:
            prefix = cls.load().login_prefix_value
            cache.set(LOGIN_PREFIX_CACHE_KEY, prefix, LOGIN_PREFIX_CACHE_SECONDS)
        return prefix


class Room(models.Model):
    number = models.PositiveIntegerField(unique=True)
    capacity = models.PositiveIntegerField(default=0, help_text="Сколько команд помещается")
    computers = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True, help_text="Использовать в рассадке")
    note = models.CharField(max_length=100, blank=True, default="")
    only_organization = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Только для команд этого вуза (например KBTU). Пусто — для всех.",
    )
    is_lecture = models.BooleanField(
        default=False,
        help_text="Лекционный зал: сильные команды сюда не садятся",
    )

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"Room {self.number}"
