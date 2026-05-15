# LeRobot

Ce dépôt est un environnement d'apprentissage pour ma montée en compétence avec le projet LeRobot de Hugging Face. Il contient également un petit package local utilisé par ces scripts (commun).

## État du projet

En développement.

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

## Structure (versionné)

- `commun/`     : fonctions réutilisables par plusieurs scripts.
- `outils/`     : scripts qui soutienne mon processus d'utilisation de LeRobot.
- `exemples/`   : scripts pédagogiques conservés comme références.
- `essais/`     : scripts exploratoires ou temporaires.
- `notes/`      : observations, jalons et commandes utiles.
- `evaluations/`: résultats d’évaluation manuels ou résumés.

## Structure (non versionné)

- `datasets/`            : datasets officialisés.
- `captures/`            : pour les différentes fichier capturés (ex. .png).
- `lerobot_ws.egg.info/` : généré par pip install -e . pour le package "commun".
- `outputs/`             : les policies sont générés ici.

