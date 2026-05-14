# Dataset v01 validé.
Résultat évaluation : 10 essais / 10 succès.
Comportement : poussée qui n'est pas fluide.
Problèmes observés : 
1. Retour en arrière avant de pousser le cube
2. Le bras fait des aller-retour 2 à 3 fois après le succès.
3. warning : boucle autour de 5,2 Hz au lieu de 30 Hz.
Résolution du problème 2 en diminuant la `duration` dans `launch.json` à 6 plutôt q'à 15

# Dataset v02 validé.
Résultat évaluation : 10 essais / 10 succès.
Comportement : poussée plus propre que v01, tâche réussie de manière stable.
Problèmes observés :
1. léger écart cumulatif lors du retour à la position initiale avant shutdown ;
2. warning persistant : boucle autour de 5,2 Hz au lieu de 30 Hz.
Impact actuel : non bloquant pour cette tâche simple.
Hypothèse principale : limite du pipeline d’évaluation/inférence plutôt que résolution caméra seule.
Décision : conserver v02 comme jalon réussi et diagnostiquer la fréquence de boucle séparément.

# Dataset v03 rejeté
L'épisode 18 est invalide. Tenté de le supprimer avec `lerobot-edit-dataset` mais un bug m'en a 
empêché. Alors l'option est de fonctionner par lots (5 épisodes par exemple) et de reprendre 
un lot si problème
Décision : on ne conserve pas ce dataset pour l'entrainement


