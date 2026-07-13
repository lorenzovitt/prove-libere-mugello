"""
Scraper per Eleven Riding Life - sito WordPress.
Pagina sorgente: https://www.elevenridinglife.com/track-days/

Ogni evento ha un link /prodotto/<slug>. Vicino al link, nello stesso
blocco, ci sono: nome pista ("Circuito di X"), data ("DD Mese YYYY"),
prezzo ("a partire da X €"), e un'icona "semaforo" che indica la
disponibilità (verde = disponibile, rosso = esaurito).

Nota: la pagina elenca ogni evento due volte (una volta nella lista
filtrabile "TUTTI" e una volta ripetuta più sotto per i filtri per pista) -
la deduplica per URL elimina il doppione.
"""

import re

from bs4 import BeautifulSoup

from .common import fetch_html, find_date, find_track

BASE_URL = "https://www.elevenridinglife.com"
CALENDAR_URL = f"{BASE_URL}/track-days/"


def scrape_elevenridinglife():
    html = fetch_html(CALENDAR_URL)
    soup = BeautifulSoup(html, "html.parser")

    events = []
    seen = set()

    for a in soup.select('a[href*="/prodotto/"]'):
        href = a.get("href", "")
        if href in seen:
            continue

        # Risaliamo di alcuni livelli nell'albero HTML per trovare il
        # blocco che contiene anche pista, data e prezzo (non solo il testo
        # del link "GO!", che da solo non basta).
        container = a
        text = ""
        img = None
        for _ in range(6):
            if container.parent is None:
                break
            container = container.parent
            text = container.get_text(" ", strip=True)
            if "a partire da" in text and re.search(r"\d{4}", text):
                img = container.find("img", src=re.compile(r"semaforo", re.IGNORECASE))
                break

        date = find_date(text)
        track = find_track(text)
        if date is None or track is None:
            continue

        day, month_name_it, year = date

        price_match = re.search(r"a partire da\s*(\d+)\s*€", text)
        price = f"{price_match.group(1)} €" if price_match else None

        availability = None
        if img is not None:
            src = img.get("src", "").lower()
            if "verde" in src:
                availability = "disponibile"
            elif "rosso" in src:
                availability = "esaurito"
            elif "giallo" in src or "arancio" in src:
                availability = "posti limitati"

        seen.add(href)
        events.append({
            "source": "Eleven Riding Life",
            "day": day,
            "month_name_it": month_name_it,
            "year": year,
            "track": track,
            "title": "Track day",
            "availability": availability,
            "price": price,
            "url": href if href.startswith("http") else BASE_URL + href,
        })

    return events


if __name__ == "__main__":
    import json
    print(json.dumps(scrape_elevenridinglife(), indent=2, ensure_ascii=False))
