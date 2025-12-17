from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import (
    landing_page,
    login_view,
    PredictImagePageView,
    PredictImageHTMLView,
    PredictionHistoryJSONView,
    CreerRapportAstreinteView,
    PreviewRapportAstreinteView,
    envoyer_rapport,
    EnvoyerAstreinteView,
    manage_contacts,
    manage_etuves,
    get_report
)

app_name = 'control'

urlpatterns = [
    path('', landing_page, name='landing'),
    path('login/', login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='control:landing'), name='logout'),
    path('predict-image-html/', PredictImagePageView.as_view(), name='predict-image-html'),
    path('predict-image-post/', PredictImageHTMLView.as_view(), name='predict-image-post'),
    path('prediction-history-json/', PredictionHistoryJSONView.as_view(), name='prediction-history-json'),
    path('creer-rapport/', CreerRapportAstreinteView.as_view(), name='creer-rapport'),
    path('creer-rapport/preview/', PreviewRapportAstreinteView.as_view(), name='preview-rapport'),
    path('envoyer-rapport/', envoyer_rapport, name='envoyer-rapport'),
    path('envoyer-astreinte/', EnvoyerAstreinteView.as_view(), name='envoyer-astreinte'),
    path('contacts/', manage_contacts, name='manage-contacts'),
    path('etuves/', manage_etuves, name='manage-etuves'),
    path('get-report/', get_report, name='get-report'),
]
