from django.contrib import admin

from .models import Bracket, Tournament


class TournamentAdmin(admin.ModelAdmin):
    # prepopulated_fields = {"slug": ("title",)}
    list_display = [
        "id",
        "title",
        "created_at",
    ]


class BracketAdmin(admin.ModelAdmin):
    list_display = ["id", "tournament"]


admin.site.register(Tournament, TournamentAdmin)
admin.site.register(Bracket, BracketAdmin)
