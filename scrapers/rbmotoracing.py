"""
Scraper SPERIMENTALE per R&B Motoracing.
Stesso identico problema di Racing Factory: la pagina calendario
(https://www.rbmotoracing.it/prove-libere) mostra solo "Caricamento..."
finché JavaScript non gira davvero. Usiamo Playwright + lo stesso approccio
"scansione testo renderizzato" spiegato in dettaglio in racingfactory.py.
"""

from .racingfactory import _extract_events_from_text

START_URL = "https://www.rbmotoracing.it/prove-libere"


def scrape_rbmotoracing():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError("Playwright non installato: impossibile leggere un sito solo-JS come questo")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(START_URL, timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)
        full_text = page.inner_text("body")
        browser.close()

    return _extract_events_from_text(full_text, "R&B Motoracing", START_URL)


if __name__ == "__main__":
    import json
    print(json.dumps(scrape_rbmotoracing(), indent=2, ensure_ascii=False))
