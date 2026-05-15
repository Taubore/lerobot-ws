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
- IMPORTANT : Utilisation de Pylance avec un niveau de vérification de types à `standard`
- Placer les scripts dans `lerobot-ws`.
- Privilégier les scripts Python exécutés dans VSCode.
- Éviter les commandes LeRobot en ligne de commande sauf si c’est beaucoup plus simple pour un diagnostic court.
- Privilégier un code lisible, maintenable, pédagogique, mais pas trop lent ni trop scolaire.
- Éviter la surconception.
- Ne pas utiliser les chaînes littérales pour les conditions, utiliser constantes, enum, dataclasses, etc. en respectant les bonnes pratiques

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

# Exécution et essais du code

- Ne pas lancer Python avec /usr/bin/python3 qui échouera. 
- Utiliser 'conda activate lerobot' ou 'conda run -n lerobot python [nom du fichier.py]'


