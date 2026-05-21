# taubore/cube_vers_zone_v001

## Objectif 

Produire une première politique LeRobot capable de pousser un cube vers une zone blanche fixe.

## Dataset cible

Nom : cube_vers_zone_v001
Tâche : Pousser latéralement le cube noir vers le carré blanc.
Stratégie : 5 lots bruts de 5 épisodes, puis fusion/officialisation
Variation : très légère variation de la position initiale du cube
Caméra : Arducam globale fixe
Zone cible : carré blanc de 7 cm x 7 cm

## Lots bruts

- lot_001 : Validé. Cube au centre.
- lot_002 : Cube 2 cm à droite.
- lot_003 : Cube 2 cm à gauche.
- lot_004 : Cube 2 cm en haut.
- lot_005 : Cube 2 cm en bas.

## Résultats de l'évaluation

Modèle : cube_vers_zone_v001_final_5000
Mode : rollout standard, sans lissage
Durée : 7 s

| Position | Essai 1 | Essai 2 | Essai 3 | Résultat | Notes |
|---|---|---|---|---|---|
| centre |S|S|S|100%|Saccadé|
| droite |S|S|S|100%|Saccadé|
| gauche |E|S|S|66%|Saccadé. Touche au bloc avec le bas de la pince. L'échec est dû car beaucoup trop bas.|
| haut |S|S|S|100%|Saccadé|
| bas |P|S|S|66%|Saccadé. Touche au bloc avec le bas de la pince, parfois ça prend, parfois non|

S = Succès  E = Échec  P = Partiel

- saccades constantes pendant le mouvement latéral.
- les micro-corrections présentes dans les démonstrations semblent amplifiées.
- micro correction ou hésitation à la fin lorsque le cube est dans la zone.

## Analyse de l'évaluation

Le défaut principal n’est pas limité à une position précise du cube.  
Les erreurs observées semblent partager une même cause : la pince descend parfois trop bas et touche le cube avec le bas de la pince au lieu de produire un contact latéral propre.

Ce contact trop bas rend la poussée moins fiable :
- à gauche, il a causé un échec franc
- en bas, il a causé une réussite partielle et une variabilité du résultat

La politique semble toutefois avoir appris la tâche générale :
- elle se dirige vers le cube
- elle pousse dans la bonne direction
- elle réussit dans la majorité des cas
- les variations centre, droite et haut sont bien couvertes

## Hypothèse :

- les micro-corrections présentes dans les démonstrations humaines sont reproduites et amplifiées par la politique
- les hésitations en fin de mouvement apparaissent surtout lorsque le cube est déjà dans la zone cible

## Décision :
- conserver le modèle comme première politique fonctionnelle
- ne pas appliquer de lissage immédiatement
- ne pas faire un lot seulement pour la position bas
- produire un lot correctif ciblé sur le contact de poussée
- inclure surtout les positions gauche et bas, où le défaut apparaît