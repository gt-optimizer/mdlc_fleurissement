import json
import os
import tempfile
from io import BytesIO

from django.conf.global_settings import DEFAULT_FROM_EMAIL
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from weasyprint import HTML
from django.conf import settings
from django.core.paginator import Paginator


from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, Spacer
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .ml_pipeline import ImageAnalysisPipeline
from .models import PredictionHistory, Phase, Etuve, Astreinte, Destinataire
from .recommandation import get_dynamic_recommendation
from .serializers import ImageUploadSerializer


# ---------------- LANDING PAGE ----------------
def landing_page(request):
    return render(request, "control/landing.html")


# ---------------- CHARGEMENT DU NOUVEAU PIPELINE ----------------
pipeline = ImageAnalysisPipeline()
try:
    pipeline.load_neural_model(
        model_path="control/model_pipeline.keras",
        classes_path="control/model_classes.pkl"
    )
    print("Model neural loaded successfully")
except Exception as e:
    print(f"Erreur lors du chargement du modèle neuronal : {e}")

_pipeline_instance = None
def get_pipeline(model_path="control/model_pipeline.pkl"):
    global _pipeline_instance
    if _pipeline_instance is None:
        p = ImageAnalysisPipeline()
        try:
            p.load_model(model_path)
        except FileNotFoundError:
            pass
        _pipeline_instance = p
    return _pipeline_instance

# ---------------- LOGIN ----------------
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Redirige vers la page d'accueil ou next
            next_url = request.GET.get('next') or 'control:landing'
            return redirect(next_url)
        else:
            # Message d'erreur pour l'UI
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
            return redirect('control:landing')
    else:
        return redirect('control:landing')


# ---------------- PREDICTION HTML ----------------
@method_decorator(login_required, name='dispatch')
class PredictImageHTMLView(View):
    def post(self, request, *args, **kwargs):
        img_file = request.FILES.get('image')
        if not img_file:
            return JsonResponse({"error": "Aucune image fournie"}, status=400)
        try:
            phase = request.POST.get('phase')
            temps_restant = request.POST.get('temps_restant')
            etuve_id = request.POST.get('etuve')
            etuve = Etuve.objects.filter(id=etuve_id).first() if etuve_id else None

            # Sauvegarde de l'image
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(img_file.name)[1]) as tmp_file:
                for chunk in img_file.chunks():
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name

            # Prédiction
            stade_pred = pipeline.predict_image_nn(tmp_path)
            print(f"Stade prédit: {stade_pred}")  # Log pour vérifier le stade prédit
            print(f"Phase: {phase}")  # Log pour vérifier la phase

            # Convertir la phase en entier
            phase_int = int(phase) if phase else 0

            # Obtenir la recommandation
            rec = get_dynamic_recommendation(stade_pred, phase_int, int(temps_restant) if temps_restant else 0)
            print(f"Recommandation: {rec}")  # Log pour vérifier la recommandation

            # Sauvegarde dans l'historique
            PredictionHistory.objects.create(
                user=request.user,
                datetime=timezone.now(),
                stade_pred=stade_pred,
                phase_etuvage=phase,
                temps_restant=int(temps_restant) if temps_restant else 0,
                recommendation=rec,
                etuve=etuve,
                image=img_file
            )

            return JsonResponse({
                "prediction": stade_pred,
                "recommendation": rec,
                "phase": phase,
                "temps_restant": temps_restant,
                "etuve": str(etuve) if etuve else None
            })
        except Exception as e:
            print(f"Erreur: {str(e)}")  # Log pour vérifier les erreurs
            return JsonResponse({"error": f"Erreur lors de la prédiction: {str(e)}"}, status=500)
        finally:
            try:
                if 'tmp_path' in locals():
                    os.remove(tmp_path)
            except Exception:
                pass


# ---------------- PREDICTION API (DRF) ----------------
class PredictImageAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, format=None):
        serializer = ImageUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        image_file = serializer.validated_data["image"]

        # Fichier temporaire
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image_file.name)[1]) as tmp:
            for chunk in image_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        try:
            # --------------------
            # NOUVEAU MODELE
            # --------------------
            pred_label = pipeline.predict_image_nn(tmp_path)
            # Pas de proba avec le modèle NN actuel
            return Response({"prediction": pred_label}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

class PredictImagePageView(View):
    def get(self, request):
        phases = Phase.objects.all().order_by('phase')
        etuves = Etuve.objects.all().order_by('id')
        return render(request, "control/predict.html", {
            "phases": phases,
            "etuves": etuves
        })

# ---------------- HISTORIQUE ----------------
@method_decorator(login_required, name='dispatch')
class PredictionHistoryJSONView(View):
    def get(self, request):
        history = PredictionHistory.objects.filter(user=request.user).order_by('-datetime')[:20]
        data = [
            {
                "datetime": h.datetime.strftime("%Y-%m-%d %H:%M"),
                "stade_pred": h.stade_pred,
                "phase_etuvage": h.phase_etuvage,
                "temps_restant": h.temps_restant,
                "recommendation": h.recommendation,
                "etuve": str(h.etuve) if h.etuve else None,
                "image_url": h.image.url if h.image else None
            }
            for h in history
        ]
        return JsonResponse(data, safe=False)

# ---------------- PAGE HTML ----------------
@method_decorator(login_required, name='dispatch')
class PredictImagePageView(View):
    def get(self, request):
        phases = Phase.objects.all().order_by('phase')
        etuves = Etuve.objects.all().order_by('id')
        return render(request, "control/predict.html", {
            "phases": phases,
            "etuves": etuves
        })


# ---------------- ASTREINTE ----------------
@method_decorator(login_required, name='dispatch')
class CreerRapportAstreinteView(View):
    def get(self, request):
        analyses = (
            PredictionHistory.objects
            .order_by("-datetime")   # les plus récentes d'abord
        )

        paginator = Paginator(analyses, 25)  # 25 lignes par page
        page_obj = paginator.get_page(request.GET.get("page"))

        return render(
            request,
            "control/creer_rapport.html",
            {
                "analyses": page_obj,   # IMPORTANT
                "page_obj": page_obj,
            }
        )

    def post(self, request):
        selected_ids = request.POST.getlist('analyses')
        commentaires = request.POST.get('commentaires', '').strip()

        if not selected_ids:
            messages.error(request, "Veuillez sélectionner au moins une analyse pour créer un rapport.")
            return redirect('control:creer-rapport')

        analyses = PredictionHistory.objects.filter(id__in=selected_ids)

        # Récupérer tous les destinataires
        destinataires = Destinataire.objects.all()

        if not destinataires:
            messages.error(request, "Aucun destinataire configuré.")
            return redirect('control:creer-rapport')

        # Création de l'astreinte enregistrée
        astreinte = Astreinte.objects.create(
            user=request.user,
            date=timezone.now(),
            commentaires=commentaires
        )
        astreinte.destinataires.set(destinataires)

        # Génération du PDF
        pdf_file = self.generate_pdf_report(analyses, commentaires, astreinte)

        # Préparation email
        subject = f"Rapport d'astreinte - {astreinte.date.strftime('%d/%m/%Y %H:%M')}"
        message = (
            "Bonjour,\n\n"
            "Veuillez trouver ci-joint le rapport d’astreinte.\n\n"
            "Cordialement,\nL'équipe Optimizer Labs"
        )

        try:
            # Envoyer le rapport à tous les destinataires
            for destinataire in destinataires:
                email = EmailMessage(
                    subject=subject,
                    body=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[destinataire.destinataire],
                )
                email.attach(
                    f"rapport_astreinte_{astreinte.date.strftime('%Y%m%d_%H%M')}.pdf",
                    pdf_file.getvalue(),
                    "application/pdf"
                )
                email.send(fail_silently=False)

            messages.success(request, "Rapport envoyé avec succès à tous les destinataires !")
        except Exception as e:
            messages.error(request, f"Erreur lors de l'envoi du mail : {e}")
            return redirect('control:creer-rapport')

        return redirect('control:creer-rapport')


    def generate_pdf_report(self, analyses, commentaires, astreinte):
        # Rendre le template HTML
        html_content = render_to_string('control/pdf_report.html', {
            'analyses': analyses,
            'commentaires': commentaires,
            'astreinte': astreinte
        })

        # Générer le PDF
        pdf_file = BytesIO()
        HTML(string=html_content, base_url=self.request.build_absolute_uri()).write_pdf(pdf_file)

        # Retourner le contenu du PDF
        pdf_file.seek(0)
        return pdf_file


def generate_pdf_report(analyses, commentaires, astreinte):
    # Rendre le template HTML
    html_content = render_to_string('control/pdf_report.html', {
        'analyses': analyses,
        'commentaires': commentaires,
        'astreinte': astreinte
    })

    # Générer le PDF
    pdf_file = BytesIO()
    HTML(string=html_content, base_url=settings.BASE_DIR).write_pdf(pdf_file)

    # Retourner le contenu du PDF
    pdf_file.seek(0)
    return pdf_file


@login_required
def envoyer_rapport(request):
    if request.method != "POST":
        return redirect("control:creer-rapport")

    try:
        selected_ids = json.loads(request.POST.get("selected_ids", "[]"))
    except json.JSONDecodeError:
        selected_ids = []

    commentaires = request.POST.get("commentaires", "")

    if not selected_ids:
        messages.error(request, "Aucune analyse sélectionnée.")
        return redirect("control:creer-rapport")

    analyses = PredictionHistory.objects.filter(id__in=selected_ids)

    destinataires = Destinataire.objects.all()  # ou ceux que tu veux

    emails = list(destinataires.values_list("destinataire", flat=True))

    if not emails:
        messages.error(request, "Aucun destinataire configuré.")
        return redirect("control:preview-rapport")

    # Création de l'astreinte enregistrée
    astreinte = Astreinte.objects.create(
        user=request.user,
        date=timezone.now(),
        commentaires=commentaires
    )
    astreinte.destinataires.set(destinataires)

    # Génération du PDF
    buffer = generate_pdf_report(analyses, commentaires, astreinte)

    # Préparation email
    subject = f"Rapport d'astreinte - {astreinte.date.strftime('%d/%m/%Y %H:%M')}"
    message = (
        "Bonjour,\n\n"
        "Veuillez trouver ci-joint le rapport d’astreinte.\n\n"
        "Cordialement,\nL'astreinteur"
    )

    try:
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=DEFAULT_FROM_EMAIL,
            to=emails,
        )
        email.attach(
            f"rapport_astreinte_{astreinte.date.strftime('%Y%m%d_%H%M')}.pdf",
            buffer.getvalue(),
            "application/pdf"
        )
        email.send()
        messages.success(request, "Rapport envoyé avec succès !")

    except Exception as e:
        messages.error(request, f"Erreur lors de l'envoi du mail : {e}")
        return redirect("control:preview-rapport")

    # Nettoyage session
    request.session.pop("rapport_data", None)

    return render(request, "control/rapport_envoye.html")




@method_decorator(login_required, name='dispatch')
class EnvoyerAstreinteView(View):
    def post(self, request):
        """Crée une astreinte et envoie un email."""
        astreinte = Astreinte.objects.create(user=request.user)
        success = generate_pdf_report(astreinte)

        if success:
            return JsonResponse({"status": "ok"})
        else:
            return JsonResponse({"status": "error", "message": "Erreur lors de l'envoi de l'email."}, status=500)


@login_required
def manage_contacts(request):
    if request.method == "POST":
        if 'delete_id' in request.POST:
            Destinataire.objects.filter(id=request.POST['delete_id']).delete()
        else:
            email = request.POST.get('email')
            if email:
                Destinataire.objects.create(destinataire=email)
        return redirect('control:manage-contacts')

    contacts = Destinataire.objects.all()
    return render(request, 'control/contacts.html', {'contacts': contacts})


@login_required
def manage_etuves(request):
    if request.method == "POST":
        numero = request.POST.get("numero")
        if numero:
            Etuve.objects.get_or_create(numero=numero)
        delete_id = request.POST.get("delete_id")
        if delete_id:
            Etuve.objects.filter(id=delete_id).delete()
        return redirect(reverse('control:manage-etuves'))

    etuves = Etuve.objects.all().order_by("numero")
    return render(request, "control/etuves.html", {"etuves": etuves})


@login_required
@csrf_exempt
def get_report(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Méthode non autorisée"}, status=405)

    try:
        data = json.loads(request.body)
        selected_ids = data.get('selected_ids', [])
        commentaires = data.get('commentaires', '')

        if not selected_ids:
            return JsonResponse({"error": "Aucune analyse sélectionnée"}, status=400)

        analyses = PredictionHistory.objects.filter(id__in=selected_ids)

        # Astreinte temporaire (non sauvegardée)
        astreinte = Astreinte(
            user=request.user,
            date=timezone.now(),
            commentaires=commentaires
        )

        html = render_to_string('control/pdf_report.html', {
            'analyses': analyses,
            'commentaires': commentaires,
            'astreinte': astreinte
        })

        return HttpResponse(html)

    except Exception as e:
        print("ERROR GET REPORT ====", e)  # Pour debug
        return JsonResponse({"error": f"Erreur lors de la génération du rapport: {str(e)}"}, status=500)
