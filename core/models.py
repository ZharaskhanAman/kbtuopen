from django.db import models
from django.contrib.auth.models import User


class Organization(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

STATUS = [
    ('pending', 'pending'),
    ('accepted', 'accepted'),
    ('rejected', 'rejected'),
]

TSHIRT_SIZE = [
    ('XS', 'XS'),
    ('S', 'S'),
    ('M', 'M'),
    ('L', 'L'),
    ('XL', 'XL'),
    ('XXL', 'XXL'),
]

class Team(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='team')
    name = models.CharField(max_length=50)
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)
    is_onsite = models.BooleanField()
    is_school_team = models.BooleanField()
    is_women_team = models.BooleanField()

    status = models.CharField(choices=STATUS, max_length=20, default='pending')
    
    def __str__(self):
        return self.name
    

class Participant(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="members")
    full_name = models.CharField(max_length=50)
    tshirt_size = models.CharField(choices=TSHIRT_SIZE, max_length=5, default='M')

    def __str__(self):
        return self.full_name