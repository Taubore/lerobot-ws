# LeRobot

Ce dépôt est un environnement d'apprentissage pour ma montée en compétence avec le projet LeRobot de Hugging Face. Il contient également un petit package local utilisé par ces scripts (commun).

## État du projet

En développement, actuellement au tout début.

## Installation locale du projet

Avant d’exécuter les scripts, activer l’environnement Python du projet avec conda, puis il faut
installer le dépôt en mode éditable pour pouvoir accéder au package "commun".

```bash
conda activate lerobot
cd /home/taubore/Projets/lerobot/lerobot-ws
python -m pip install -e .
```

Pour les scripts qui configurent une caméra USB avec V4L2, installer aussi les outils système :

```bash
sudo apt install v4l-utils
```

## Utilisation

Les scripts stables sont dans `references/`. Les scripts de dataset initialisent l'Arducam avant
l'ouverture par LeRobot afin de demander explicitement le mode vidéo, par exemple MJPG
1280 x 720 à 15 FPS.

Le script `references/dataset/inspecter_dataset_pilote.py` vérifie les épisodes, les durées,
les champs essentiels et les dimensions des données principales avant un premier entraînement.

Les configurations de débogage VSCode dans `.vscode/launch.json` demandent `dataset.repo_id` et
le nombre d'étapes au lancement. Ces deux valeurs sont ensuite réutilisées pour construire les
chemins du dataset, des sorties d'entraînement et de la policy évaluée.

## Structure (versionné)

- commun/               → diverses fonctions pouvant être réutilisées
- brouillons/           → code non nettoyé et temporaire
- datasets/             → jeux de données
- essais/               → apprentissage progressif et tests temporaires
- notes/                → explications, observations, commandes utiles
- references/           → scripts propres, stables, pédagogiques

## Structure (non versionné)

- captures/             → pour les différentes fichier capturés (ex. .png)
- lerobot_ws.egg.info/  → généré par pip install -e . pour le package "commun" 
- outputs/              → les policies sont générés ici

# Critères pour qu’un script aille dans le dossier references/

- Il fonctionne
- Il a un objectif unique
- Il ne contient pas de vieux essais commentés
- Il affiche clairement ce qu’il fait
- Il se termine proprement
- Il peut être relu dans trois mois sans devoir deviner son intention

