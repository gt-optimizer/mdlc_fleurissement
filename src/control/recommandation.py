def get_dynamic_recommendation(prediction, phase, temps_restant_minutes):
    """
    Retourne une recommandation selon le stade prédit, la phase d'étuvage et le temps restant.
    prediction : str (ex: "stade1", "stade2", "stade3", "stade4", "stade5")
    phase : int (ex: 7, 8, 9, 10)
    temps_restant_minutes : int (minutes)
    """
    # Exemple de règles basées sur les prédictions et les phases
    if phase == 1 or phase == 2 or phase == 3 or phase == 4 or phase == 5 or phase == 6:  # Phase de séchage
        if prediction == "stade1":
            return "Tout est normal, ne rien faire"
        elif prediction == "stade2":
            return "Voir fonctionnement étuve et courbes. Si l'étuve ne marche pas, changer d'étuve et relancer l'étuve dans la phase 9."
        elif prediction == "stade3":
            return "Voir fonctionnement étuve et courbes. Si l'étuve ne marche pas, changer d'étuve et relancer l'étuve dans la phase 9."
        elif prediction == "stade4":
            return "Voir fonctionnement étuve et courbes. Si l'étuve ne marche pas, changer d'étuve et relancer l'étuve dans la phase 9."
        elif prediction == "stade5":
            return "Voir fonctionnement étuve et courbes. Si l'étuve ne marche pas, changer d'étuve et relancer l'étuve dans la phase 9."
        else:
            return "Reprendre une photo, stade de fleurissement non détecté"

    elif phase == 7:  # Phase de montée en température
        if prediction == "stade3" or prediction == "stade4" or prediction == "stade5":
            return "Voir fonctionnement étuve et courbes. Si l'étuve ne marche pas, changer d'étuve et relancer l'étuve dans la phase 9."
        else:
            return "Tout est normal, ne rien faire"

    elif phase == 8:  # Phase de fleurissement
        if prediction == "stade1" and temps_restant_minutes >= 1440:
            return "Ne rien faire, revoir l'étuve le lendemain."
        elif prediction == "stade1" and temps_restant_minutes < 1440:
            return "Rallonger la phase 8 pour qu'il y ait au moins 24h restantes."
        elif prediction == "stade2" and temps_restant_minutes >= 1440:
            return "Ne rien faire, revoir l'étuve le lendemain."
        elif prediction == "stade2" and temps_restant_minutes < 1440:
            return "Rallonger la phase 8 pour qu'il y ait au moins 24h restantes."
        elif prediction == "stade3" or prediction == "stade4" or prediction == "stade5":
            return "Faire un saut de phase, passer en phase 9."
        else:
            return "Vérifier les conditions générales de l'étuve."

    elif phase == 9:  # Phase de refroidissement
        if prediction == "stade1":
            return "Retour en phase 8."
        else:
            return "Tout est normal, ne rien faire"

    elif phase == 10:  # Phase finale
        return "Ne rien faire, noter sur le cahier d'astreinte si pas fleuri."

    else:
        return "Reprendre une photo, stade de fleurissement non détecté ou phase inconnue"