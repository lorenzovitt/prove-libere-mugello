"""
Scraper per Promo Racing - calendario prove libere moto.
Pagina sorgente: https://www.promoracing.it/en/calendar/bike

Strategia: la pagina elenca gli eventi come link <a> il cui href contiene
"/calendar/bike.<ID>/...". Il testo del link contiene, nell'ordine:
disponibilità, giorno, mese (abbreviato inglese), titolo evento, circuito.
Non ci basiamo su classi CSS (troppo fragili nel tempo) ma su pattern di testo,
che tendono a essere più stabili.
"""

import re

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.promoracing.it"
CALENDAR_URL = f"{BASE_URL}/en/calendar/bike"

AVAILABILITY_MAP = {
    "Available": "disponibile",
    "Limited availability": "posti limitati",
    "Sold Out": "esaurito",
}

MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Sul sito, il nome del circuito è sempre l'ultima parte del testo del link
# e finisce con la parola "Circuit" (es. "Mugello Circuit", "Misano World
# Circuit"). Usiamo questo pattern invece di una lista fissa di piste, così
# se l'agenzia aggiunge nuovi circuiti li rileviamo automaticamente.
TRACK_PATTERN = re.compile(r"([A-Z][A-Za-zÀ-ÿ' ]*Circuit)\s*$")


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
}


def scrape_promoracing():
    try:
        resp = requests.get(CALENDAR_URL, timeout=20, headers=HEADERS)
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"connessione fallita verso {CALENDAR_URL}: {exc}") from exc

    if resp.status_code != 200:
        # Includiamo status code e un pezzo di risposta: aiuta a distinguere
        # un blocco anti-bot (spesso pagina HTML di "Access denied"/captcha)
        # da un errore diverso.
        snippet = resp.text[:300].replace("\n", " ")
        raise RuntimeError(
            f"HTTP {resp.status_code} da {CALENDAR_URL} — inizio risposta: {snippet!r}"
        )

    soup = BeautifulSoup(resp.text, "html.parser")

    events = []
    seen = set()

    for a in soup.select('a[href*="/calendar/bike."]'):
        href = a.get("href", "")
        if "#" not in href:
            # link "genitore" senza giorno specifico, salta
            continue

        text = " ".join(a.stripped_strings)
        if not text:
            continue

        avail_match = re.search(r"(Available|Limited availability|Sold Out)", text)
        month_match = re.search(r"\b(" + "|".join(MONTHS_EN) + r")\b", text)
        track_match = TRACK_PATTERN.search(text)
        # Il giorno lo prendiamo dall'ancora dell'URL (#06, #17...) che è più affidabile
        # del primo numero trovato nel testo.
        day_match = re.search(r"#(\d{1,2})$", href)

        if not (avail_match and month_match and track_match and day_match):
            continue

        title = text
        for m in (avail_match, month_match, track_match):
            title = title.replace(m.group(0), "")
        title = re.sub(r"\b\d{1,2}\b", "", title).strip(" -|")

        day = int(day_match.group(1))
        month_abbr = month_match.group(1)
        track = track_match.group(1)

        dedup_key = (href.split("#")[0], day)
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        events.append({
            "source": "Promo Racing",
            "source_url": CALENDAR_URL,
            "day": day,
            "month_abbr": month_abbr,
            "track": track,
            "availability_raw": avail_match.group(1),
            "availability": AVAILABILITY_MAP.get(avail_match.group(1), avail_match.group(1)),
            "title": title or "Motorcycle trackday",
            "price": None,  # non mostrato in lista, servirebbe la pagina di dettaglio
            "url": href if href.startswith("http") else BASE_URL + href,
        })

    return events


if __name__ == "__main__":
    import json
    print(json.dumps(scrape_promoracing(), indent=2, ensure_ascii=False))
