"""
Scraper per MotoRacePeople - sito statico.
Pagina sorgente: https://www.motoracepeople.com/about

Gli eventi sono un elenco compatto di link tipo:
"17_18_19 LUGLIO - MUGELLO - TURNI CRONOMETRATI - PAREGGIAMENTI"
Per date multiple (es. "17_18_19") prendiamo solo il primo giorno come data
di inizio evento.

NOTA: come Gully Racing, questa pagina non mostra prezzo né disponibilità
per singolo evento: questi campi restano vuoti, non è un errore.
"""

from bs4 import BeautifulSoup

from .common import fetch_html, find_date, find_track

BASE_URL = "https://www.motoracepeople.com"
CALENDAR_URL = f"{BASE_URL}/about"


def scrape_motoracepeople():
    html = fetch_html(CALENDAR_URL)
    soup = BeautifulSoup(html, "html.parser")

    events = []
    seen = set()

    for a in soup.find_all("a", href=True):
        text = a.get_text(" ", strip=True)
        if not text:
            continue

        date = find_date(text)
        track = find_track(text)
        if date is None or track is None:
            continue

        href = a["href"]
        if href in seen:
            continue
        seen.add(href)

        day, month_name_it, year = date

        events.append({
            "source": "MotoRacePeople",
            "day": day,
            "month_name_it": month_name_it,
            "year": year,
            "track": track,
            "title": text,
            "availability": None,
            "price": None,
            "url": href if href.startswith("http") else BASE_URL + href,
        })

    return events


if __name__ == "__main__":
    import json
    print(json.dumps(scrape_motoracepeople(), indent=2, ensure_ascii=False))
