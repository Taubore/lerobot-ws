# LeRobot

Ce dépôt est un environnement d'apprentissage pour ma montée en compétence avec le projet
LeRobot de Hugging Face. Il contient également un petit package local utilisé par ces scripts
(`commun`).

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

- `~/.cache/huggingface/lerobot/{repo_id}` : lots bruts d'enregistrement LeRobot.
- `datasets/`            : datasets officialisés après validation ou fusion de lots.
- `captures/`            : pour les différentes fichier capturés (ex. .png).
- `lerobot_ws.egg.info/` : généré par pip install -e . pour le package "commun".
- `outputs/`             : les policies sont générés ici.

## Enregistrement de datasets

Le script `outils/enregistrer_dataset.py` sert à enregistrer des lots bruts avec un SO-101 leader,
un SO-101 follower et une caméra globale Arducam.

Les ports, identifiants de bras, paramètres caméra et valeurs par défaut d'enregistrement sont
centralisés dans `outils/config_lerobot_ws.toml`.

Il laisse LeRobot stocker le lot dans son cache local :
`~/.cache/huggingface/lerobot/{repo_id}`. Il ne pousse pas le dataset vers Hugging Face Hub et
refuse de démarrer si `push_to_hub = true`. Les datasets validés ou fusionnés seulement doivent
être placés dans `datasets/`.

Si un lot existe déjà dans le cache, le script permet d'annuler, de supprimer le lot existant ou
de saisir un nouveau nom de lot.

Contrôles pendant l'enregistrement :

- flèche droite : accepter l'épisode ou passer à l'étape suivante ;
- flèche gauche : annuler et recommencer l'épisode courant ;
- `ESC` : arrêter la session, encoder les vidéos et terminer proprement.

Par défaut, le script masque les sorties verbeuses de LeRobot et de l'encodeur vidéo pendant
l'enregistrement. Pour les réafficher lors d'un diagnostic, passer la constante `VERBOSE` à
`True` dans `outils/enregistrer_dataset.py`.

## Exécution de politiques

Le script `outils/executer_politique.py` permet de tester plusieurs fois une politique
entraînée sans relancer une configuration VSCode. Il demande le nom d'un entraînement local sous
`/home/taubore/Projets/lerobot/lerobot-ws/outputs/train`, charge le checkpoint
`checkpoints/last/pretrained_model`, puis lance un essai à chaque appui sur `Espace`.

```bash
python lerobot-ws/outils/executer_politique.py
```

Les paramètres de workspace, entraînement, matériel, caméra, politique par défaut, tâche et durée
sont lus dans `outils/config_lerobot_ws.toml` via `commun/config_lerobot.py`.
Le paramètre `[execution_politique].interpolation_multiplier` règle l'interpolation d'actions
LeRobot pour lisser les mouvements pendant l'exécution.

## Vérification de datasets

Le script `outils/verifier_dataset.py` charge un lot brut depuis le cache LeRobot ou un dataset
officialisé depuis le workspace avec `LeRobotDataset`. Il affiche un résumé technique, les
statistiques de durée des épisodes et une suggestion pour `[execution_politique].duree_s`.

Si la vérification réussit, il écrit aussi un manifeste Markdown `manifeste.md` dans le dossier
du dataset vérifié.
