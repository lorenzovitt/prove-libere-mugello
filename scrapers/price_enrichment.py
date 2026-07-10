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

PRICE_PATTERN = re.compile(r"\d{1,4}(?:[.,]\d{2})?\s*€")


def enrich_prices(events, max_events=30):
    to_enrich = [e for e in events if not e.get("price") and e.get("url")][:max_events]
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

                    match = PRICE_PATTERN.search(page.content())
                    if match:
                        ev["price"] = match.group(0).replace(" ", "")
                        print(f"[INFO] Prezzo trovato per {ev['url']}: {ev['price']}")
                    else:
                        print(f"[INFO] Nessun prezzo trovato in pagina per {ev['url']}")

                except Exception as exc:  # noqa: BLE001
                    print(f"[INFO] Impossibile recuperare il prezzo per {ev.get('url')}: {exc}")

            browser.close()

    except Exception as exc:  # noqa: BLE001
        print(f"[INFO] Arricchimento prezzi non disponibile in questa esecuzione: {exc}")

    return events
