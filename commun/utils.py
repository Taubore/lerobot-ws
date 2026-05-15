'''
Regroupe un ensemble de fonctions utilitaires génériques qu'il est possible d'utiliser dans une
multitude d'autres projets.
'''

import readline

def saisir_avec_texte_defaut(invite: str, texte_defaut: str) -> str:
    """
    Saisir un texte en préremplissant la ligne avec une valeur par défaut.
    """

    readline.set_startup_hook(lambda: readline.insert_text(texte_defaut))

    try:
        return input(invite)

    finally:
        readline.set_startup_hook()
