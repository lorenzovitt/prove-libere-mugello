"""
Scraper per Gully Racing - sito statico.
Pagina sorgente: https://www.gullyracing.it/calendario (homepage in fallback)

NOTA: prezzo e disponibilità non sono mostrati in questa pagina (il prezzo
compare solo nella pagina "buoni pista", non è legato al singolo evento).
Questi due campi restano quindi vuoti per questa agenzia: è normale, non un
errore. Se necessario si può aggiungere in futuro l'apertura della pagina
di ogni singolo evento per cercare il prezzo lì.
"""

from bs4 import BeautifulSoup

from .common import fetch_html, find_date, find_track

BASE_URL = "https://www.gullyracing.it"
CALENDAR_URL = f"{BASE_URL}/calendario"


def scrape_gullyracing():
    html = fetch_html(CALENDAR_URL)
    soup = BeautifulSoup(html, "html.parser")

    events = []
    seen = set()

    for a in soup.select('a[href*="/evento/"], a[href*="/prodotto?id="]'):
        href = a.get("href", "")
        if href in seen:
            continue

        # Risaliamo nell'albero per trovare il blocco con data e pista.
        container = a
        text = ""
        for _ in range(5):
            if container.parent is None:
                break
            container = container.parent
            text = container.get_text(" ", strip=True)
            if "PROVE" in text.upper():
                break

        date = find_date(text)
        track = find_track(text)
        if date is None or track is None:
            continue

        day, month_name_it, year = date
        seen.add(href)

        events.append({
            "source": "Gully Racing",
            "day": day,
            "month_name_it": month_name_it,
            "year": year,
            "track": track,
            "title": "Prove cronometrate",
            "availability": None,
            "price": None,
            "url": href if href.startswith("http") else BASE_URL + href,
        })

    return events


if __name__ == "__main__":
    import json
    print(json.dumps(scrape_gullyracing(), indent=2, ensure_ascii=False))
