from django.db import models
from django.contrib.auth.models import User
from .telegram import send_message
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

    def __str__(self):
        return self.name

    @property
    def login(self):
        return f"kbtuspring25-{self.id}"

    def generate_cf_format(self):
        members = ",".join(str(member) for member in self.members.all())
        name = self.name
        if self.is_women_team:
            name += "[W]"
        if self.is_school_team:
            name += "[S]"
        team_name = f"{self.organization}: {name} - {members}"

        return f"CONTEST_ID| {self.login} | {self.password} | {team_name}"

    def send_credentials_by_telegram(self):
        (status, response) = send_message(
            self.owner.username, self.login, self.password, self.seat
        )

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

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
