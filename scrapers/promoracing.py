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

TRACKS = ["Mugello Circuit", "Misano World Circuit", "Cremona Circuit"]


def scrape_promoracing():
    resp = requests.get(CALENDAR_URL, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
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
        track_match = re.search(r"(" + "|".join(TRACKS) + r")", text)
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
