# taubore/[nom dataset]

## Objectif 

[Description de l'objectif]

## Dataset cible

Nom : [nom dataset]
Tâche : [nom de la tâche tel que décrit dans le fichier de config]

## Lots bruts

- lot_001 : 
- lot_002 : 
...

## Résultats de l'évaluation

Modèle : [nom modèle]
Mode : rollout standard, interpolation à 2
Durée : 10 s

| Position | Essai 1 | Essai 2 | Essai 3 | Résultat | Notes |
|---|---|---|---|---|---|
| centre ||||||
| droite ||||||
| gauche ||||||
| haut ||||||
| bas ||||||

S = Succès  E = Échec  P = Partiel


## Analyse de l'évaluation


## Hypothèse :


## Décision :



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


# taubore/cube_vers_zone_v001_contact_5000

Mode : rollout standard, sans lissage  
Durée : 7 s  

Résumé :
- 20 essais physiques réalisés ;
- 3 à 5 essais par position ;
- 1 seul échec observé ;
- échec en position haut ;
- réussite globale approximative : 95 %.

## Analyse :
Le lot correctif `lot_006_contact` semble avoir amélioré la robustesse de la politique.  
Le défaut de contact trop bas observé lors de l’évaluation précédente semble moins présent ou moins problématique.

La politique reste saccadée pendant le mouvement latéral, mais les saccades semblent légèrement moins marquées qu’avec le modèle précédent.

## Conclusion :
- la politique est maintenant fonctionnelle et relativement robuste pour la tâche actuelle ;
- la correction ciblée du dataset a été utile ;
- aucun besoin immédiat de refaire tout le dataset ;
- la prochaine amélioration doit viser la fluidité, sans dégrader le taux de réussite.

## Décision :
- conserver ce modèle comme nouvelle référence ;
- ne pas ajouter immédiatement un nouveau lot correctif ;
- tester ensuite une amélioration de fluidité par évaluation lissée ou par données plus fluides.

# taubore/cube_dans_boite_v004

## Objectif 

Apprendre une première tâche complète de pick-and-place : saisir le cube dans le carré blanc,
le soulever, le transporter vers une boîte rectangulaire noire et le déposer dans la boîte.

## Dataset cible

Nom : taubore/cube_dans_boite_v004
Tâche : prendre le cube et le déposer dans la boîte noire

## Lots bruts

- lot_001 : 5 épisodes, cube au centre, boîte fixe, trajectoire de référence.
- lot_002 : 5 épisodes, petites variations du cube dans le carré blanc, boîte fixe.

## Résultats de l'évaluation

Modèle : cube_dans_boite_v004_5000
Mode : rollout standard, interpolation à 2
Durée : 15 s

| Position | Essai 1 | Essai 2 | Essai 3 | Résultat | Notes |
|---|---|---|---|---|---|
| centre |P|E|P|Pas très bon|Prise du cube, mais passé près de le perdre, car trop à droite. Cube tombé à l'extérieur de la boite (haut, gauche)|
| droite |S|S|E|Succès, mais fragile|La prise à droite semble un peu plus facile, mais demeure fragile. Lorsque succès du cube dans la boite, celui-ci passait près d'être à l'extérieur, car la pince était trop à gauche de la boite.|
| gauche |E|E|E|Incapable de prendre le cube|Prise trop à droite, la pince gauche touchait le milieu du cube. Prise impossible. Le robot, voyais qu'il n'avais pas le cube et tentait de se reprendre, mais la limite de temps arrivait avant qu'il s'essait une 2e fois.|
| avant |S|S|E|Peut-être là où ça semble le plus facile|Lors de l'échec, le cube a roulé dans la pince. Il l'a donc perdu.|
| arrière |E|E|E|Incapable de prendre le cube|Comme les autres, il est trop à droite, la pince gacuhe vient frapper le milieu du cube. Prise impossible de cette façon|

S = Succès  E = Échec  P = Partiel

Problèmes observés:
- Prise souvent trop à droite. La pince touche le centre du cube qui se déplace vers la gauche, alors la prise est impossible.
- POur le dépôt dans la boite, le cube est souvent trop en haut à gauche de la boite et il tombe donc à côté. S'il n'y avait pas ce problème, le mouvement semble quand même plutôt bon.
- Mouvement hésitant et un peu saccadé, mais ce n'est pas ce qui est le problème le plus important.

## Analyse de l'évaluation

La policy réussit parfois, mais le comportement n'est pas assez fiable pour être conservé
comme policy de référence.

Le problème principal est systématique : la prise se fait trop à droite du cube. La pince
gauche touche souvent le centre du cube, ce qui pousse le cube vers la gauche et empêche
une prise stable. Ce problème apparaît surtout lorsque le cube est à gauche ou en arrière.

Le dépôt présente aussi un biais : lorsque le cube est transporté jusqu'à la boîte, il arrive
souvent trop haut et trop à gauche. Plusieurs essais auraient pu réussir si la position de
dépôt avait été légèrement mieux centrée.

Le mouvement hésitant et saccadé existe, mais il n'est pas le problème prioritaire. La policy
semble avoir appris une trajectoire générale utile, mais avec un mauvais alignement spatial
pour la prise et le dépôt.

## Hypothèse :

Le dataset contient probablement trop peu de variations corrigées autour des cas difficiles,
surtout cube à gauche et cube en arrière. La policy a appris une trajectoire moyenne qui passe
trop à droite du cube et qui dépose trop haut à gauche dans la boîte.

Le lot actuel est donc insuffisant pour généraliser correctement à toutes les positions testées.
Il faut ajouter des épisodes ciblés, pas recommencer complètement.

## Décision :

Ne pas officialiser `cube_dans_boite_v004_5000` comme policy réussie.

Conserver le dataset `cube_dans_boite_v004` comme base de travail, mais créer un lot de
correction ciblé avant le prochain entraînement.

Correction prioritaire :
- ajouter des épisodes où le cube est à gauche ;
- ajouter des épisodes où le cube est en arrière ;
- forcer une prise plus centrée sur le cube ;
- forcer un dépôt plus centré dans la boîte, légèrement moins haut et moins à gauche ;
- garder la boîte fixe ;
- ne pas changer la résolution caméra ;
- ne pas changer de policy architecture.

Prochaine policy proposée : `cube_dans_boite_v004_10000` ou `cube_dans_boite_v005_5000`,
selon que le nouveau lot est ajouté au dataset existant ou utilisé pour créer une version
corrigée documentée.