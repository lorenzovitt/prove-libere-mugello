"""
Scraper per Race Action - homepage con eventi scritti come testo libero
dentro tag <h2>, non come prodotti/link individuali.
Pagina sorgente: https://www.raceaction.it

ATTENZIONE - questo è il sito meno strutturato del gruppo:
- non esiste un link diretto alla pagina del singolo evento (le
  prenotazioni si fanno via email/WhatsApp), quindi il campo "url" punta
  semplicemente all'homepage;
- la disponibilità è dedotta da parole chiave nel testo (es. "SOLD OUT",
  "posti disponibili") che potrebbero cambiare formulazione nel tempo;
- il prezzo è preso dall'ultimo importo in euro scritto nel titolo
  dell'evento (di solito il prezzo promo aggiornato, ma non è garantito).

Se in futuro il sito cambia struttura, è probabile che sia questo scraper a
rompersi per primo: in tal caso va rivisto con calma guardando l'HTML reale.
"""

from bs4 import BeautifulSoup

from .common import fetch_html, find_date, find_track

BASE_URL = "https://www.raceaction.it"


def scrape_raceaction():
    html = fetch_html(BASE_URL)
    soup = BeautifulSoup(html, "html.parser")

    events = []

    for h2 in soup.find_all("h2"):
        text = h2.get_text(" ", strip=True)

        date = find_date(text)
        track = find_track(text)
        if date is None or track is None:
            continue

        day, month_name_it, year = date

        prices = __import__("re").findall(r"(\d{2,4})\s*€", text)
        price = f"{prices[-1]} €" if prices else None

        # Guardiamo il testo successivo (fino al prossimo h2, se c'è) per
        # capire lo stato di disponibilità.
        collected = []
        node = h2
        for _ in range(40):
            node = node.find_next_sibling()
            if node is None or node.name == "h2":
                break
            collected.append(node.get_text(" ", strip=True))
        following_text = " ".join(collected).lower()

        if "sold out" in following_text or "esaurit" in following_text:
            availability = "esaurito"
        elif "meno di" in following_text and "post" in following_text:
            availability = "posti limitati"
        elif "post" in following_text and "dispon" in following_text:
            availability = "disponibile"
        else:
            availability = None

        events.append({
            "source": "Race Action",
            "day": day,
            "month_name_it": month_name_it,
            "year": year,
            "track": track,
            "title": text[:80],
            "availability": availability,
            "price": price,
            "url": BASE_URL,
        })

    return events


if __name__ == "__main__":
    import json
    print(json.dumps(scrape_raceaction(), indent=2, ensure_ascii=False))
