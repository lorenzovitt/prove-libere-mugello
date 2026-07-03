"""
Script principale: lancia tutti gli scraper, normalizza le date,
filtra solo Mugello, ordina cronologicamente e salva docs/data.json
(la cartella docs/ è quella pubblicata da GitHub Pages).

Aggiungere un nuovo sito sorgente in futuro = scrivere uno scraper in
scrapers/nome_agenzia.py che esporti una funzione che ritorna una lista di
dict con almeno i campi: day, e uno tra (month_abbr in inglese) o
(month_name_it in italiano) o month (numero 1-12) + year opzionale.
Poi aggiungerlo qui sotto in ALL_SCRAPERS.
"""

import json
import sys
import traceback
from datetime import date

from scrapers.promoracing import scrape_promoracing
from scrapers.rossocorsa import scrape_rossocorsa

MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTHS_IT = [
    "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
    "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre",
]

# Ogni scraper è isolato: se uno fallisce (es. sito cambiato), gli altri
# continuano a funzionare e va solo a log l'errore, invece di bloccare tutto.
ALL_SCRAPERS = {
    "Promo Racing": scrape_promoracing,
    "Rosso Corsa": scrape_rossocorsa,
}

MUGELLO_KEYWORD = "mugello"


def infer_year(month_num, today):
    """Se il mese indicato è già passato quest'anno, assume sia l'anno prossimo."""
    year = today.year
    if month_num < today.month:
        year += 1
    return year


def normalize_event(ev, today):
    month_num = None
    if ev.get("month_abbr"):
        try:
            month_num = MONTHS_EN.index(ev["month_abbr"]) + 1
        except ValueError:
            month_num = None
    elif ev.get("month_name_it"):
        try:
            month_num = MONTHS_IT.index(ev["month_name_it"]) + 1
        except ValueError:
            month_num = None
    elif ev.get("month"):
        month_num = int(ev["month"])

    if month_num is None:
        return None

    year = ev.get("year") or infer_year(month_num, today)

    try:
        event_date = date(year, month_num, ev["day"])
    except ValueError:
        return None

    return {
        "date": event_date.isoformat(),
        "source": ev.get("source"),
        "track": ev.get("track"),
        "title": ev.get("title"),
        "availability": ev.get("availability"),
        "price": ev.get("price"),
        "url": ev.get("url"),
    }


def run():
    today = date.today()
    raw_events = []
    errors = []

    for name, fn in ALL_SCRAPERS.items():
        try:
            raw_events.extend(fn())
        except Exception as exc:  # noqa: BLE001
            errors.append(name)
            print(f"[ATTENZIONE] Scraper '{name}' fallito: {exc}", file=sys.stderr)
            traceback.print_exc()

    normalized = []
    for ev in raw_events:
        n = normalize_event(ev, today)
        if n is None:
            continue
        if MUGELLO_KEYWORD not in (n["track"] or "").lower():
            continue
        if n["date"] < today.isoformat():
            continue  # niente eventi passati
        normalized.append(n)

    normalized.sort(key=lambda e: e["date"])

    output = {
        "generated_at": today.isoformat(),
        "sources_failed": errors,
        "events": normalized,
    }

    with open("docs/data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"OK: salvati {len(normalized)} eventi al Mugello in docs/data.json")
    if errors:
        print(f"ATTENZIONE: {len(errors)} scraper falliti: {', '.join(errors)}")


if __name__ == "__main__":
    run()
