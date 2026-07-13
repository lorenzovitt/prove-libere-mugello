"""
Arricchimento prezzi per eventi che non lo espongono nella pagina calendario
(es. Promo Racing, dove il prezzo compare solo dopo aver cliccato sulla data
specifica, caricato via JavaScript).

Usa Playwright (browser headless) per aprire davvero la pagina, provare a
cliccare sull'opzione del giorno giusto, e cercare un prezzo nel contenuto
reso. È un meccanismo "best effort":
- se Playwright non è installato, salta silenziosamente (nessun crash)
- se una pagina non risponde come previsto, quell'evento resta senza prezzo
- NON blocca mai l'esecuzione principale dello script

NOTA IMPORTANTE: la logica di "click sul giorno giusto" è basata su come è
strutturata la pagina di dettaglio al momento in cui è stata scritta questa
funzione (link testuali tipo "August 29th Saturday"). Se non funziona,
guardare il log stampato per capire cosa succede pagina per pagina, e
sistemare il selettore di conseguenza.
"""

import re

# Un prezzo valido per una giornata in pista è sempre un importo consistente
# (tipicamente 80-400 €). Cerchiamo SOLO numeri con almeno 2 cifre prima di
# "€", ed escludiamo comunque tutto sotto i 50 € più sotto nel codice: prima
# provavamo a matchare qualsiasi "N €" nell'HTML grezzo, ma questo prendeva
# spesso numeri piccoli senza relazione col prezzo reale (es. "5€" da un
# badge, un costo accessorio, o un elemento nascosto nella pagina).
PRICE_PATTERN = re.compile(r"\d{2,4}(?:[.,]\d{2})?\s*€")
MIN_PLAUSIBLE_PRICE = 50


def _plausible_price(match_text):
    number = re.match(r"\d+", match_text)
    return number is not None and int(number.group(0)) >= MIN_PLAUSIBLE_PRICE


def enrich_prices(events, max_events=30):
    # Se più eventi condividono lo stesso URL (es. Race Action, che non ha
    # pagine per singolo evento), aprire quella pagina non ci direbbe a
    # quale dei tanti eventi appartiene il prezzo trovato: meglio saltare
    # questi casi piuttosto che rischiare di assegnare un prezzo sbagliato.
    url_counts = {}
    for e in events:
        if e.get("url"):
            url_counts[e["url"]] = url_counts.get(e["url"], 0) + 1

    to_enrich = [
        e for e in events
        if not e.get("price") and e.get("url") and url_counts.get(e["url"]) == 1
    ][:max_events]
    if not to_enrich:
        return events

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[INFO] Playwright non installato: salto l'arricchimento prezzi.")
        return events

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()

            for ev in to_enrich:
                try:
                    page.goto(ev["url"], timeout=25000, wait_until="networkidle")

                    day_num = str(int(ev["date"].split("-")[2]))  # es. "29", niente zero iniziale
                    day_pattern = re.compile(rf"^{day_num}(st|nd|rd|th)\b", re.IGNORECASE)
                    option = page.get_by_text(day_pattern)

                    if option.count() > 0:
                        option.first.click()
                        page.wait_for_timeout(800)

                    # Cerchiamo nel testo VISIBILE della pagina (non nell'HTML
                    # grezzo, che contiene script/meta/elementi nascosti che
                    # possono generare falsi positivi), e scartiamo i match
                    # troppo piccoli per essere un prezzo plausibile.
                    visible_text = page.inner_text("body")
                    candidates = [m for m in PRICE_PATTERN.findall(visible_text) if _plausible_price(m)]

                    if candidates:
                        ev["price"] = candidates[0].replace(" ", "")
                        print(f"[INFO] Prezzo trovato per {ev['url']}: {ev['price']}")
                    else:
                        print(f"[INFO] Nessun prezzo plausibile trovato per {ev['url']}")

                except Exception as exc:  # noqa: BLE001
                    print(f"[INFO] Impossibile recuperare il prezzo per {ev.get('url')}: {exc}")

            browser.close()

    except Exception as exc:  # noqa: BLE001
        print(f"[INFO] Arricchimento prezzi non disponibile in questa esecuzione: {exc}")

    return events
