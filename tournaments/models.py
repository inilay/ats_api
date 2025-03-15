from django.db import models

from profiles.models import Profile

# class Tournament(models.Model):
#     title = models.CharField(max_length=255)
#     content = models.TextField()
#     slug = models.SlugField(max_length=255, unique=True)
#     participants = models.TextField()
#     poster = models.ImageField(upload_to='photos/media/%Y/%m/%d/', blank=True)
#     game = models.CharField(max_length=255)
#     prize = models.FloatField()
#     created_at = models.DateTimeField(auto_now_add=True)
#     owner = models.ForeignKey(Profile, related_name='tournaments', on_delete=models.CASCADE)
#     start_time = models.DateTimeField()

#     def save(self, *args, **kwargs):
#         self.slug = slugify(self.title)
#         # if not self.poster:
#         #     self.poster = f'tournament_def_{random.randint(1, 13)}.png'
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return self.title

#     def get_absolute_url(self):
#         return reverse('tournament', kwargs={'slug': self.slug})


# class Bracket(models.Model):

#     tournament = models.ForeignKey('Tournament', related_name='brackets', on_delete=models.CASCADE, null=True)
#     bracket = models.JSONField(blank=True)
#     final = models.BooleanField(default=True)
#     participants_from_group = models.IntegerField(default=0)

#     class BracketType(models.TextChoices):
#         SINGLEELIMINATION = 'SE', _('Single elimination')
#         DOUBLEELIMINATION = 'DE', _('Double elimination')
#         ROUNDROBIN = 'RR', _('Round robin')
#         SWISS = 'SW', _('Swiss')

#     type = models.CharField(
#         max_length=255,
#         choices=BracketType.choices,
#         default=BracketType.SINGLEELIMINATION,
#     )

#     def __str__(self):
#         return self.type


class Tournament(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField(null=True)
    link = models.SlugField(max_length=255, unique=True)
    poster = models.ImageField(upload_to="photos/media/%Y/%m/%d/", blank=True)
    game = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    start_time = models.DateTimeField()
    owner = models.ForeignKey(Profile, related_name="tournaments", on_delete=models.CASCADE)
    type = models.ForeignKey("TournamentType", on_delete=models.CASCADE)
    moderators = models.ManyToManyField(Profile, related_name="administrated_tournaments")
    followers = models.ManyToManyField(Profile, related_name="subscriptions")


class TournamentNotification(models.Model):
    tournament = models.OneToOneField("Tournament", related_name="notification", on_delete=models.CASCADE)
    task_id = models.CharField(max_length=255)
    in_queue = models.BooleanField(default=False)


class TournamentType(models.Model):
    name = models.CharField(max_length=255)


class Bracket(models.Model):
    tournament = models.ForeignKey(
        "Tournament", related_name="brackets", on_delete=models.CASCADE, blank=True, null=True
    )
    bracket_type = models.ForeignKey("BracketType", related_name="brackets", on_delete=models.CASCADE)
    participant_in_match = models.IntegerField(default=2)


class AnonymousBracket(models.Model):
    link = models.SlugField(max_length=255, unique=True)
    bracket = models.OneToOneField("Bracket", related_name="anonymous_bracket", on_delete=models.CASCADE)


class GroupBracketSettings(models.Model):
    participant_in_group = models.IntegerField()
    advance_from_group = models.IntegerField()
    final_bracket = models.ForeignKey("Bracket", related_name="final_brackets", on_delete=models.CASCADE)
    group_brackets = models.ManyToManyField("Bracket", related_name="group_brackets")


class SEBracketSettings(models.Model):
    bracket = models.ForeignKey("Bracket", related_name="se_settings", on_delete=models.CASCADE)
    advances_to_next = models.IntegerField(default=1)


class RRBracketSettings(models.Model):
    bracket = models.ForeignKey("Bracket", related_name="rr_settings", on_delete=models.CASCADE)
    points_per_loss = models.IntegerField(default=0)
    points_per_draw = models.IntegerField(default=0)
    points_per_victory = models.IntegerField(default=1)


class SWBracketSettings(models.Model):
    bracket = models.ForeignKey("Bracket", related_name="sw_settings", on_delete=models.CASCADE)
    points_per_loss = models.IntegerField(default=0)
    points_per_draw = models.IntegerField(default=0)
    points_per_victory = models.IntegerField(default=1)


class BracketType(models.Model):
    name = models.CharField(max_length=255)


class Round(models.Model):
    bracket = models.ForeignKey("Bracket", related_name="rounds", on_delete=models.CASCADE)
    serial_number = models.IntegerField()


class Match(models.Model):
    round = models.ForeignKey("Round", related_name="matches", on_delete=models.CASCADE)
    state = models.ForeignKey("MatchState", on_delete=models.CASCADE)
    start_time = models.DateTimeField(null=True)
    serial_number = models.IntegerField()


class MatchState(models.Model):
    name = models.CharField(max_length=255)


class MatchParticipantInfo(models.Model):
    match = models.ForeignKey("Match", related_name="info", on_delete=models.CASCADE)
    participant_score = models.IntegerField()
    participant = models.CharField(max_length=255)
    participant_result = models.ForeignKey("ParticipantResult", on_delete=models.CASCADE, default=1)


class ParticipantResult(models.Model):
    name = models.CharField(max_length=255)
