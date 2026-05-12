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