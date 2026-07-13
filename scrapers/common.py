"""
Utilità condivise tra tutti gli scraper: elenco piste conosciute (per
riconoscerle nel testo indipendentemente da come le scrive ogni sito) e
mesi in italiano/inglese.
"""

import re

MONTHS_IT = [
    "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
    "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre",
]
MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Parola chiave (minuscolo) -> nome canonico da mostrare. Stessa lista usata
# da main.py per unificare le varianti tra agenzie diverse.
TRACK_ALIASES = {
    "mugello": "Mugello",
    "misano": "Misano",
    "cremona": "Cremona",
    "vallelunga": "Vallelunga",
    "imola": "Imola",
    "franciacorta": "Franciacorta",
    "adria": "Adria",
    "magione": "Magione",
    "varano": "Varano de' Melegari",
    "modena": "Modena",
    "pergusa": "Pergusa",
    "binetto": "Binetto",
    "castelletto": "Castelletto di Branduzzo",
    "nuvolari": "Tazio Nuvolari",
    "pomposa": "Pomposa",
    "cervesina": "Cervesina",
    "barcellona": "Barcellona",
    "catalunya": "Barcellona",
    "aragon": "Aragon",
    "jerez": "Jerez",
    "alcarras": "Alcarrás",
    "alcarrás": "Alcarrás",
    "siviglia": "Siviglia",
    "sevilla": "Siviglia",
    "almeria": "Almería",
    "almería": "Almería",
    "cartagena": "Cartagena",
}

MONTHS_IT_PATTERN = "|".join(MONTHS_IT)


def find_track(text):
    """Cerca nel testo una delle piste conosciute e ne ritorna il nome
    canonico. Più robusto di provare a isolare posizionalmente il nome
    pista con una regex, perché non dipende da dove si trova nel testo."""
    if not text:
        return None
    lower = text.lower()
    for keyword, canonical in TRACK_ALIASES.items():
        if keyword in lower:
            return canonical
    return None


def find_date(text):
    """Cerca la prima occorrenza di 'giorno (+ eventuali altri giorni
    separati da _/- ) + mese in italiano' (ed eventualmente l'anno) nel
    testo. Ritorna (day, month_name_it, year) oppure None se non trovato.
    In caso di range o date multiple (es. 'dal 04 al 06 Settembre',
    '17_18_19 Luglio') cattura solo il primo giorno.

    I lookaround (?<!\\d) / (?!\\d) evitano di interpretare come "giorno" un
    pezzo di un numero più lungo che non è una data, es. il codice prodotto
    "Nuvolari 2805" (altrimenti "05" seguito da "- 13 Luglio" verrebbe letto
    come inizio di un range di date, sbagliando)."""
    match = re.search(
        rf"(?<!\d)(\d{{1,2}})(?!\d)(?:[\s_/-]+(?<!\d)\d{{1,2}}(?!\d))*\s+({MONTHS_IT_PATTERN})(?:\s+(\d{{4}}))?",
        text,
        re.IGNORECASE,
    )
    if not match:
        return None
    day = int(match.group(1))
    month_name_it = match.group(2).lower()
    year = int(match.group(3)) if match.group(3) else None
    return day, month_name_it, year


BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
}


def fetch_html(url, timeout=20):
    """GET con header realistici e un errore chiaro (status + inizio
    risposta) in caso di problema, così è facile capire dal log se è un
    blocco anti-bot o altro."""
    import requests

    try:
        resp = requests.get(url, timeout=timeout, headers=BROWSER_HEADERS)
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"connessione fallita verso {url}: {exc}") from exc

    if resp.status_code != 200:
        snippet = resp.text[:300].replace("\n", " ")
        raise RuntimeError(f"HTTP {resp.status_code} da {url} — inizio risposta: {snippet!r}")

    return resp.text
