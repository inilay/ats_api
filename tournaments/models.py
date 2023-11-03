from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from profiles.models import Profile
import random
import json


class Tournament(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    slug = models.SlugField(max_length=255, unique=True)
    participants = models.TextField()
    poster = models.ImageField(upload_to='photos/media/%Y/%m/%d/', blank=True)
    game = models.CharField(max_length=255)
    prize = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(Profile, related_name='tournaments', on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    
    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        # if not self.poster:
        #     self.poster = f'tournament_def_{random.randint(1, 13)}.png'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('tournament', kwargs={'slug': self.slug})


class Bracket(models.Model):

    tournament = models.ForeignKey('Tournament', related_name='brackets', on_delete=models.CASCADE, null=True)
    bracket = models.JSONField(blank=True)
    final = models.BooleanField(default=True)
    participants_from_group = models.IntegerField(default=0)
    
    class BracketType(models.TextChoices):
        SINGLEELIMINATION = 'SE', _('Single elimination')
        DOUBLEELIMINATION = 'DE', _('Double elimination')
        ROUNDROBIN = 'RR', _('Round robin')
        SWISS = 'SW', _('Swiss')

    type = models.CharField(
        max_length=255,
        choices=BracketType.choices,
        default=BracketType.SINGLEELIMINATION,
    )

    def __str__(self):
        return self.type


