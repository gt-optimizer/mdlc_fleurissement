import datetime

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Phase(models.Model):
    phase = models.DecimalField(decimal_places=0, max_digits=2, unique=True)

    def __str__(self):
        return f"Phase {int(self.phase)}"

class Temps_restant(models.Model):
    temps_restant = models.TimeField(
        blank=True,
        null=True,
        default=datetime.time(0, 0)  # 0h 0min par défaut
    )

    def __str__(self):
        return f"{self.temps_restant}"

class Recommendation(models.Model):
    texte = models.TextField()  # La recommandation à afficher

    def __str__(self):
        return self.texte


class Etuve(models.Model):
    numero = models.DecimalField(max_digits=3, decimal_places=0, blank=True, null=True)

    def __str__(self):
        if self.numero is None:
            return "Étuve (non numérotée)"
        return f"Étuve {int(self.numero)}"


class PredictionHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now_add=True)
    stade_pred = models.CharField(max_length=255)
    phase_etuvage = models.CharField(max_length=255, blank=True, null=True)
    temps_restant = models.IntegerField(default=0)
    recommendation = models.TextField(blank=True, null=True)
    etuve = models.ForeignKey('Etuve', on_delete=models.SET_NULL, blank=True, null=True)
    image = models.ImageField(upload_to='prediction_images/', blank=True, null=True)

    def __str__(self):
        return f"{self.datetime} - {self.stade_pred} - {self.user.username}"


class Destinataire(models.Model):
    destinataire = models.EmailField(max_length=10, blank=True, null=True)
    def __str__(self):
        return f"{self.destinataire}"


class Astreinte(models.Model):
    date = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    destinataires = models.ManyToManyField("Destinataire", blank=True)
    commentaires = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Astreinte {self.id} - {self.user.username} - {self.date.strftime('%Y-%m-%d %H:%M')}"
