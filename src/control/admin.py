from django.contrib import admin

from .models import Recommendation, Phase, Temps_restant, PredictionHistory, Etuve


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('texte',)


@admin.action(description="Corriger les phases invalides")
def fix_invalid_phases(modeladmin, request, queryset):
    for p in queryset:
        try:
            float(p.phase)  # test de conversion
        except Exception:
            p.phase = 0
            p.save()

class PhaseAdmin(admin.ModelAdmin):
    list_display = ("id", "phase")
    actions = [fix_invalid_phases]

admin.site.register(Phase, PhaseAdmin)

@admin.register(Temps_restant)
class TempsRestantAdmin(admin.ModelAdmin):
    list_display = ('temps_restant',)

@admin.register(PredictionHistory)
class PredictionHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'stade_pred', 'phase_etuvage', 'temps_restant', 'recommendation', 'datetime')
    list_filter = ('user', 'datetime', 'stade_pred')
    search_fields = ('user__username', 'stade_pred', 'recommendation')
    ordering = ('-datetime',)

@admin.register(Etuve)
class EtuveAdmin(admin.ModelAdmin):
    list_display = ('numero',)
