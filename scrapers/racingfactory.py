"""
Scraper SPERIMENTALE per Racing Factory.
Il sito (https://www.racingfactory.it) è una Single Page Application: la
pagina HTML statica è vuota, tutto il contenuto viene caricato via
JavaScript. Non è quindi possibile usare requests+BeautifulSoup come per
gli altri siti: serve un browser headless (Playwright) per renderizzare
davvero la pagina.

Non conoscendo la struttura esatta del DOM una volta renderizzato (non
verificabile senza eseguire JavaScript in prima persona), invece di
indovinare selettori CSS specifici (rischio alto di sbagliare ed estrarre
zero eventi, o peggio dati sbagliati), analizziamo il TESTO della pagina
già renderizzata cercando pattern generici: "giorno + mese" vicino al nome
di una pista conosciuta. È un approccio robusto alla struttura del DOM ma
meno preciso nell'associare correttamente prezzo/disponibilità a ogni
evento - per questo qui non proviamo a estrarli, restano vuoti.

Se dopo il primo run reale il numero di eventi trovati è 0 o palesemente
sbagliato, guardare il log e probabilmente serve aggiustare l'URL di
partenza (potrebbe non essere la homepage) o il modo in cui viene atteso
il caricamento della pagina.
"""

import re

from .common import MONTHS_IT_PATTERN, TRACK_ALIASES

START_URL = "https://www.racingfactory.it/"


def _extract_events_from_text(full_text, source_name, event_url):
    """Cerca tutte le occorrenze 'giorno + mese' nel testo e, per ciascuna,
    verifica se una pista conosciuta compare entro una finestra di testo
    vicina (150 caratteri prima o dopo). Se sì, genera un evento."""
    events = []
    seen = set()

    for m in re.finditer(rf"(\d{{1,2}})\s+({MONTHS_IT_PATTERN})(?:\s+(\d{{4}}))?", full_text, re.IGNORECASE):
        window_start = max(0, m.start() - 150)
        window_end = min(len(full_text), m.end() + 150)
        window = full_text[window_start:window_end].lower()

        track = None
        for keyword, canonical in TRACK_ALIASES.items():
            if keyword in window:
                track = canonical
                break
        if track is None:
            continue

        day = int(m.group(1))
        month_name_it = m.group(2).lower()
        year = int(m.group(3)) if m.group(3) else None

        dedup_key = (day, month_name_it, year, track)
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        price_match = re.search(r"(\d{2,4})\s*€", window)

        events.append({
            "source": source_name,
            "day": day,
            "month_name_it": month_name_it,
            "year": year,
            "track": track,
            "title": "Prove libere / track day",
            "availability": None,
            "price": f"{price_match.group(1)} €" if price_match else None,
            "url": event_url,
        })

    return events


def scrape_racingfactory():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError("Playwright non installato: impossibile leggere un sito solo-JS come questo")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(START_URL, timeout=30000, wait_until="networkidle")
        page.wait_for_timeout(1500)  # margine extra per eventuali chiamate JS lente
        full_text = page.inner_text("body")
        browser.close()

    return _extract_events_from_text(full_text, "Racing Factory", START_URL)


if __name__ == "__main__":
    import json
    print(json.dumps(scrape_racingfactory(), indent=2, ensure_ascii=False))
