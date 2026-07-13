"""
Script principale: lancia tutti gli scraper, normalizza le date,
ordina cronologicamente e salva docs/data.json (la cartella docs/ è quella
pubblicata da GitHub Pages).

Tutte le piste vengono raccolte: il filtro per pista è lato frontend
(docs/index.html), così l'utente può scegliere quale vedere senza dover
toccare questo script.

Aggiungere un nuovo sito sorgente in futuro = scrivere uno scraper in
scrapers/nome_agenzia.py che esporti una funzione che ritorna una lista di
dict con almeno i campi: day, e uno tra (month_abbr in inglese) o
(month_name_it in italiano) o month (numero 1-12) + year opzionale.
Poi aggiungerlo qui sotto in ALL_SCRAPERS.
"""

import json
import re
import sys
import traceback
from datetime import date

from scrapers.promoracing import scrape_promoracing
from scrapers.rossocorsa import scrape_rossocorsa
from scrapers.primainpista import scrape_primainpista
from scrapers.elevenridinglife import scrape_elevenridinglife
from scrapers.gullyracing import scrape_gullyracing
from scrapers.motoracepeople import scrape_motoracepeople
from scrapers.raceaction import scrape_raceaction
from scrapers.racingfactory import scrape_racingfactory
from scrapers.rbmotoracing import scrape_rbmotoracing
from scrapers.price_enrichment import enrich_prices
from scrapers.common import MONTHS_IT, TRACK_ALIASES

MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTHS_IT_ABBR = ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"]

_DATE_WORDS = {m.lower() for m in MONTHS_EN} | set(MONTHS_IT) | set(MONTHS_IT_ABBR)


def clean_track_name(raw):
    """Normalizza il nome pista: unifica le varianti note tramite l'elenco
    condiviso in scrapers/common.py, e in ogni caso ripulisce numeri e nomi
    di mese eventualmente rimasti attaccati per errore durante l'estrazione
    (es. 'Mugello 09 Oct')."""
    if not raw:
        return None

    lower = raw.lower()
    for keyword, canonical in TRACK_ALIASES.items():
        if keyword in lower:
            return canonical

    # Pista non in elenco: pulizia generica come fallback, per non far
    # comparire nel filtro voci tipo "09 Oct" o doppioni con spazi diversi.
    text = re.sub(r"\d+", "", raw)
    words = [w for w in text.split() if w.strip(",.;:").lower() not in _DATE_WORDS]
    text = " ".join(words)
    text = re.sub(r"\s{2,}", " ", text).strip(" -|,")
    return text or None

# Ogni scraper è isolato: se uno fallisce (es. sito cambiato), gli altri
# continuano a funzionare e va solo a log l'errore, invece di bloccare tutto.
# Racing Factory e R&B Motoracing sono sperimentali (siti solo-JS, scraping
# via browser headless): possono fallire più facilmente degli altri.
ALL_SCRAPERS = {
    "Promo Racing": scrape_promoracing,
    "Rosso Corsa": scrape_rossocorsa,
    "Prima in Pista": scrape_primainpista,
    "Eleven Riding Life": scrape_elevenridinglife,
    "Gully Racing": scrape_gullyracing,
    "MotoRacePeople": scrape_motoracepeople,
    "Race Action": scrape_raceaction,
    "Racing Factory": scrape_racingfactory,
    "R&B Motoracing": scrape_rbmotoracing,
}


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
        "track": clean_track_name(ev.get("track")),
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
        if n["date"] < today.isoformat():
            continue  # niente eventi passati
        normalized.append(n)

    normalized.sort(key=lambda e: e["date"])

    # Per gli eventi senza prezzo (es. Promo Racing, che lo mostra solo via
    # JS dopo aver cliccato la data) proviamo a recuperarlo con un browser
    # headless. Se fallisce per qualche motivo, l'evento resta senza prezzo
    # ma con il link diretto al sito: non è un errore bloccante.
    normalized = enrich_prices(normalized)

    output = {
        "generated_at": today.isoformat(),
        "sources_failed": errors,
        "events": normalized,
    }

    with open("docs/data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"OK: salvati {len(normalized)} eventi in docs/data.json")
    if errors:
        print(f"ATTENZIONE: {len(errors)} scraper falliti: {', '.join(errors)}")


if __name__ == "__main__":
    run()
