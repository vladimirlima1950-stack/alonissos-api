import json
import os

ARQUIVO_TRANSLATIONS = os.path.join(
    os.path.dirname(__file__),
    "translations.json"
)

with open(ARQUIVO_TRANSLATIONS, "r", encoding="utf-8") as f:
    translations = json.load(f)


def t(chave, idioma):

    valor = translations

    for parte in chave.split("."):
        valor = valor[parte]

    return valor[idioma]