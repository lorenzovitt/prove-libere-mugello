"""
Scraper per Prima in Pista - negozio Squarespace.
Pagina sorgente: https://www.primainpista.it/shop

Ogni evento è un prodotto del negozio, con link tipo /shop/p/<slug> e un
titolo del tipo "Cremona Circuit - 24 Agosto - Turni Piloti Licenziati" o
"4 DISPONIBILI - Tazio Nuvolari 2805 - 13 luglio - PROMO 2". Estraiamo pista,
data e prezzo dal testo del link, che è più stabile delle classi CSS.
Prodotti senza una data (es. "Buono regalo", "Giornate a Pomposa" senza data
specifica) vengono scartati automaticamente perché non matchano il pattern
data.
"""

import re

from bs4 import BeautifulSoup

from .common import fetch_html, find_date, find_track

BASE_URL = "https://www.primainpista.it"
SHOP_URL = f"{BASE_URL}/shop"


def scrape_primainpista():
    html = fetch_html(SHOP_URL)
    soup = BeautifulSoup(html, "html.parser")

    events = []
    seen = set()

    for a in soup.select('a[href*="/shop/p/"]'):
        href = a.get("href", "")
        if href in seen:
            continue

        text = " ".join(a.stripped_strings)
        if not text:
            continue

        date = find_date(text)
        if date is None:
            continue  # prodotto senza data specifica (buono regalo, ecc.)

        day, month_name_it, year = date
        track = find_track(text)
        if track is None:
            continue

        seen.add(href)

        # Prezzo: se c'è uno sconto ("Prezzo scontato: X €") prendiamo quello,
        # altrimenti il primo prezzo trovato nel testo.
        scontato_match = re.search(r"Prezzo scontato:\s*(\d+[.,]\d{2})\s*€", text)
        if scontato_match:
            price = scontato_match.group(1) + " €"
        else:
            price_match = re.search(r"(\d+[.,]\d{2})\s*€", text)
            price = price_match.group(1) + " €" if price_match else None

        # Disponibilità: "X DISPONIBILI" o "X disponibili" da qualche parte nel testo.
        avail_match = re.search(r"(\d+)\s*disponibil[ei]", text, re.IGNORECASE)
        if "esaurit" in text.lower() or "sold out" in text.lower():
            availability = "esaurito"
        elif avail_match:
            availability = f"{avail_match.group(1)} disponibili"
        else:
            availability = None

        events.append({
            "source": "Prima in Pista",
            "day": day,
            "month_name_it": month_name_it,
            "year": year,
            "track": track,
            "title": "Prove libere",
            "availability": availability,
            "price": price,
            "url": href if href.startswith("http") else BASE_URL + href,
        })

    return events


if __name__ == "__main__":
    import json
    print(json.dumps(scrape_primainpista(), indent=2, ensure_ascii=False))
