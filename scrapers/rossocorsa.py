"""
Scraper per Rosso Corsa - calendario prove libere moto.
Pagina sorgente: https://www.rossocorsaonline.com/prove

Strategia: la pagina elenca gli eventi come link <a> il cui href contiene
"/prove/detail/<ID>". Il testo del link ha il pattern:
"13 LUGLIO | MUGELLO a partire da 309,00€ PRENOTA!"
(a volte con range tipo "03-31 DICEMBRE").

NOTA: la disponibilità (posti disponibili / in esaurimento / esauriti) su
questo sito non è visibile come testo semplice nella lista eventi (potrebbe
essere un'icona o un colore CSS). Questo scraper NON estrae la disponibilità
per ora: se serve, va ispezionata la pagina reale (HTML sorgente) per capire
come viene marcata, es. classe tipo "disponibile"/"esaurito" su un elemento
vicino al link, o "alt" di un'icona.
"""

import re

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.rossocorsaonline.com"
CALENDAR_URL = f"{BASE_URL}/prove"

MONTHS_IT = [
    "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
    "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre",
]


def scrape_rossocorsa():
    resp = requests.get(CALENDAR_URL, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    events = []
    seen = set()

    for a in soup.select('a[href*="/prove/detail/"]'):
        href = a.get("href", "")
        text = " ".join(a.stripped_strings)
        if not text:
            continue

        # Es: "13 LUGLIO | MUGELLO a partire da 309,00€ PRENOTA!"
        # Es. range: "03-31 DICEMBRE | BUONI REGALO PRENOTA!"
        date_match = re.search(
            r"(\d{1,2})(?:-(\d{1,2}))?\s+(" + "|".join(MONTHS_IT) + r")",
            text,
            re.IGNORECASE,
        )
        track_match = re.search(r"\|\s*([A-ZÀ-Ý' ]+?)\s*(?:a partire da|PRENOTA)", text, re.IGNORECASE)
        price_match = re.search(r"(\d+[.,]\d{2})\s*€", text)

        if not (date_match and track_match):
            continue

        day = int(date_match.group(1))
        month_name_it = date_match.group(3).lower()
        track = track_match.group(1).strip().title()

        dedup_key = href
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        events.append({
            "source": "Rosso Corsa",
            "source_url": CALENDAR_URL,
            "day": day,
            "month_name_it": month_name_it,
            "track": track,
            "availability_raw": None,
            "availability": "da verificare sul sito",  # vedi nota in testa al file
            "title": "Prova libera",
            "price": (price_match.group(1).replace(".", ",") + " €") if price_match else None,
            "url": href if href.startswith("http") else BASE_URL + href,
        })

    return events


if __name__ == "__main__":
    import json
    print(json.dumps(scrape_rossocorsa(), indent=2, ensure_ascii=False))
