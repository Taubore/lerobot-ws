## Environnement

- Linux : `Ubuntu 24.04`
- VSCode
- Profil VSCode : `LeRobot`
- Environnement Python : `Miniforge/conda` sous `lerobot`
- Python : `3.12.3`
- Bibliothèque : `lerobot`
- Projet personnel sur GitHub : https://github.com/Taubore/lerobot-ws

# Règles d'environnement de développement

- Garder Git/GitHub propre : branches simples, commits fréquents, messages de commit en français.
- Maintenir un fichier README.md à jour en respectant les bonnes pratiques de développement communautaire (GitHub).
- Ne pas créer de nouveaux fichiers ou dossiers sans besoin réel.
- Faire des changements petits, lisibles et faciles à tester.

## Règles de code générales 

- Utiliser Python
- Placer les scripts dans `lerobot-ws`.
- Privilégier les scripts Python exécutés dans VSCode.
- Éviter les commandes LeRobot en ligne de commande sauf si c’est beaucoup plus simple pour un diagnostic court.
- Privilégier un code lisible, maintenable, pédagogique, mais pas trop lent ni trop scolaire.
- Éviter la surconception.
- Ne pas utiliser les chaînes littérales pour les conditions, utiliser constantes, enum, dataclasses, etc. en respectant les bonnes pratiques

## Vérification de types avec Pylance

- IMPORTANT : le projet utilise Pylance avec un niveau de vérification de types à `standard`.
- Le code ajouté ou modifié doit être compatible avec Pylance `standard` sans diagnostics rouges connus.
- Ne pas ignorer un avertissement Pylance en supposant que l’exécution fonctionne quand même.
- Si Pylance signale une erreur de type, corriger le typage ou la structure du code plutôt que masquer le problème.
- Éviter les conversions directes depuis `object`, par exemple `int(valeur)`, `float(valeur)` ou `str(valeur)`, sauf si le type a été vérifié avant.
- Utiliser `Any` seulement quand la valeur vient réellement d’une bibliothèque externe mal typée ou dynamique, et garder une validation explicite à l’exécution.
- Préférer des annotations précises : `Path`, `dict[str, Any]`, `list[str]`, `float | None`, dataclasses, enums ou constantes typées selon le besoin.
- Quand une API externe retourne un type incertain, isoler la conversion dans une petite fonction dédiée avec un nom clair et une validation lisible.
- Ne pas utiliser `# type: ignore` sauf en dernier recours, avec un commentaire expliquant pourquoi le typage ne peut pas être exprimé proprement.
- Après une modification Python, lancer au minimum :
  `conda run -n lerobot python -m py_compile chemin/du/script.py`
- Si une erreur Pylance est rapportée par l’utilisateur, la corriger avant toute autre amélioration non essentielle.

## Style du code

- Utiliser des identifiants en français sans accents.
- Commentaires en français.
- Commentaires, docstrings et textes utilisateur en français normal avec accents.
- Utiliser des docstrings multilignes.
- Conserver en anglais les éléments imposés par Python et les autres modules utilisés.
- Limiter les lignes à 100 caractères. 
- Code bien aéré et suffisament documenté en respectant les bonne pratiques de développement communautaire (GitHub).

## Règles de code spécifiques à la robotique

- Connexion explicite au matériel.
- Lecture d’observation.
- Action simple et progressive seulement si nécessaire.
- Pauses explicites avec `sleep()`.
- Messages lisibles.
- Déconnexion propre avec `finally`.

# Architecture

- L'architecture demeure simple, se référer au README.md pour la structure et s'assurer de la
respecter lors d'ajout de nouveaux fichiers sources.
- Si une évolution d'architecture apparaît nécessaire, demander une confirmation avant.
- Si une fonction est d'un usage générique au delà de ce projet : commun/utils.py
- Si une fonction est d'un usage générique pour ce projet : commun/utils_lerobot.py
- En cas de doute sur le caractère générique d'une nouvelle fonction à créer, le demander.

## Gestion des chemins et de la configuration

- Ne pas coder en dur les chemins liés au workspace, aux datasets, aux sorties ou aux caches.
- Utiliser `outils/config_lerobot_ws.toml` comme source de vérité pour les chemins propres au projet.
- Utiliser `commun/config_lerobot.py` pour lire la configuration, et faire évoluer ce module si une nouvelle section TOML devient nécessaire.
- Pour les chemins fournis par LeRobot ou Hugging Face, utiliser les constantes ou API du SDK quand elles existent, par exemple `HF_LEROBOT_HOME`.
- Ajouter un paramètre dans `config_lerobot_ws.toml` seulement si le chemin est réellement propre au projet et n’est pas déjà fourni par une bibliothèque.
- Les constantes Python doivent rester limitées aux valeurs très locales au script : choix de menu, libellés, seuils simples, préfixes de features.
- Une constante ne doit pas servir à masquer une configuration durable ou un chemin que l’utilisateur pourrait vouloir modifier.
- Avant d’ajouter un chemin dans le code, chercher d’abord :
  - s’il existe déjà dans `config_lerobot_ws.toml`;
  - s’il est déjà exposé par `commun/config_lerobot.py`;
  - s’il est fourni par le SDK LeRobot ou Hugging Face.
- Si une nouvelle configuration est nécessaire, modifier le TOML, ajouter la dataclass correspondante dans `commun/config_lerobot.py`, puis utiliser cette configuration dans les scripts.


## Exécution des essais

- Ne pas lancer Python avec /usr/bin/python3 qui échouera. 
- Utiliser 'conda activate lerobot' ou 'conda run -n lerobot python [nom du fichier.py]'
- Privilégier les tests réalistes du projet plutôt que des validations trop théoriques.
- Quand une commande Python pertinente nécessite un accès hors bac à sable, demander directement une autorisation persistante pour le préfixe approprié, par exemple : `conda run`
- Pour ce projet, l’autorisation persistante du préfixe `conda run` est souhaitée afin de tester les scripts avec l’environnement `lerobot`.
- Ne pas s’arrêter à une validation syntaxique si un test réel court et non destructif est possible.
- Les tests réels doivent éviter d’altérer les sorties importantes : datasets, checkpoints, modèles entraînés, sorties d’évaluation et caches non liés au test.
- Les tests qui écrivent uniquement les fichiers normalement produits par le script testé sont acceptables si l’impact est clair et limité.
- Ne jamais lancer d’action destructive sans accord explicite : suppression, déplacement, fusion irréversible, nettoyage de cache, réinitialisation Git.
- Ne jamais lancer d’action longue ou coûteuse sans accord explicite : entraînement, téléchargement massif, évaluation longue, enregistrement robot prolongé.
- Si un test réaliste peut être fait avec un dataset local existant et sans modifier son contenu métier, le privilégier.


## Préférences d’autorisation

- Quand l’outil demande une autorisation, proposer un préfixe persistant raisonnable plutôt qu’une autorisation ponctuelle si cela réduit les interruptions futures.
- Préfixe persistant recommandé pour ce projet :
  `conda run`
- Ne pas proposer de préfixe persistant trop large comme `python`, `python3`, `bash`, `rm` ou une commande destructive.

