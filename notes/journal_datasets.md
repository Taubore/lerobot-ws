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

## Évaluation
centre  : 
droite  :
gauche  :
haut    :
bas     :

S = Succès
E = Échec
P = Partiel

- saccades constantes pendant le mouvement latéral
- les micro-corrections présentes dans les démonstrations semblent amplifiées

## Analyse de l'évaluation



## Hypothèse :
- la politique reproduit les micro-corrections humaines avec trop de variations entre actions successives

## Décision :
- conserver le dataset et le modèle
- tester d’abord un lissage léger des actions côté évaluation