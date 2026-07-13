# Prove libere moto Mugello — aggregatore

Sito che raccoglie automaticamente le date delle prove libere moto al Mugello
da più agenzie e le mostra in un'unica tabella. Aggiornamento automatico
ogni 8 ore, costo zero, hosting su GitHub Pages, embeddabile in Framer.

## Come funziona

```
scrapers/promoracing.py    → estrae le date dal sito Promo Racing
scrapers/rossocorsa.py     → estrae le date dal sito Rosso Corsa
main.py                    → lancia gli scraper, filtra solo Mugello,
                              unisce e ordina le date, salva docs/data.json
docs/index.html            → pagina che legge data.json e mostra la tabella
.github/workflows/update.yml → GitHub Actions: rilancia main.py ogni 8 ore
                                e committa il nuovo data.json automaticamente
```

## Deploy (tutto gratuito)

1. **Crea un account GitHub** (se non ce l'hai già) su github.com.
2. **Crea un nuovo repository pubblico**, es. `prove-libere-mugello`.
3. Carica dentro tutti i file di questo progetto (mantenendo la struttura
   delle cartelle) — puoi trascinarli direttamente dall'interfaccia web di
   GitHub, oppure con git:
   ```
   git init
   git add .
   git commit -m "Prima versione"
   git branch -M main
   git remote add origin https://github.com/TUO-USERNAME/prove-libere-mugello.git
   git push -u origin main
   ```
4. **Attiva GitHub Pages**: nel repository vai su
   `Settings → Pages → Build and deployment → Source: Deploy from a branch`,
   poi scegli branch `main` e cartella `/docs`. Salva.
   Dopo 1-2 minuti il sito sarà visibile su:
   `https://TUO-USERNAME.github.io/prove-libere-mugello/`
5. **Il workflow automatico è già incluso** (`.github/workflows/update.yml`):
   GitHub Actions rilancerà gli scraper ogni 8 ore da solo, gratuitamente
   (i repository pubblici hanno minuti Actions illimitati per uso standard).
   Puoi anche avviarlo manualmente subito: tab **Actions** del repository →
   seleziona il workflow → **Run workflow**, per popolare `data.json` senza
   aspettare 8 ore.

## Integrazione in Framer

Nel tuo progetto Framer, aggiungi un componente **Embed** e inserisci:

```html
<iframe
  src="https://TUO-USERNAME.github.io/prove-libere-mugello/"
  style="width:100%; height:600px; border:none;">
</iframe>
```

Oppure, se preferisci che il contenuto erediti lo stile grafico di Framer
invece di avere un design proprio, si può in un secondo momento convertire
`docs/index.html` in un componente Framer (codice React) che fa `fetch` dello
stesso `data.json` — dimmelo se vuoi che prepari anche questa versione.

## Agenzie incluse e affidabilità stimata

| Agenzia | Come viene letta | Prezzo | Disponibilità | Affidabilità |
|---|---|---|---|---|
| Promo Racing | HTML statico | via browser headless (best effort) | ✅ | 🟢 Alta |
| Rosso Corsa | HTML statico | ✅ | ⚠️ non esposta dal sito | 🟢 Alta |
| Prima in Pista | HTML statico (Squarespace) | ✅ | ✅ | 🟢 Alta |
| Eleven Riding Life | HTML statico (WordPress) | ✅ | ✅ (icona semaforo) | 🟢 Alta |
| Gully Racing | HTML statico | ⚠️ non mostrato in lista | ⚠️ non mostrata | 🟡 Media |
| MotoRacePeople | HTML statico | ⚠️ non mostrato in lista | ⚠️ non mostrata | 🟡 Media |
| Race Action | HTML statico ma testo libero, non strutturato | ✅ (da titolo) | ✅ (da parole chiave) | 🟠 Bassa — nessun link diretto all'evento, solo email/WhatsApp |
| Racing Factory | **Sito solo-JavaScript**, letto via browser headless con pattern generici | ⚠️ raramente | ⚠️ non affidabile | 🔴 Sperimentale |
| R&B Motoracing | **Sito solo-JavaScript**, letto via browser headless con pattern generici | ⚠️ raramente | ⚠️ non affidabile | 🔴 Sperimentale |

Le ultime due sono contrassegnate come sperimentali perché il sito non espone nessun contenuto nell'HTML statico (serve eseguire JavaScript per vederlo), e senza poter ispezionare dal vivo la struttura esatta della pagina resa, l'estrazione si basa su pattern di testo generici invece che su selettori precisi. **Vanno testate dopo il primo deploy** guardando il log del workflow.



## Aggiungere altre agenzie in futuro

Per aggiungerne altre:

1. Copia lo scraper più simile come base (`scrapers/rossocorsa.py` se il
   sito è HTML statico e ben strutturato, `scrapers/raceaction.py` se è
   testo libero, `scrapers/racingfactory.py` se il sito è tutto in
   JavaScript). Il modulo `scrapers/common.py` contiene funzioni riutilizzabili
   (`find_date`, `find_track`, `fetch_html`) che coprono già la maggior
   parte dei casi.
2. Adatta i pattern di estrazione al testo/HTML di quel sito.
3. Aggiungi la nuova funzione in `main.py`, dentro `ALL_SCRAPERS`.
4. Se il sito usa un nome pista non ancora in elenco, aggiungilo a
   `TRACK_ALIASES` in `scrapers/common.py`.
5. Fai commit e push: al giro successivo (max 8 ore, o subito se lanci il
   workflow a mano) la nuova agenzia comparirà nella tabella.

## Limiti noti / cose da verificare dopo il primo deploy

- **Rosso Corsa**: la disponibilità (posti disponibili/esauriti) non è
  estraibile dal solo testo della pagina lista — probabilmente è mostrata
  con un'icona o un colore. Nel dubbio lo scraper segna
  "da verificare sul sito" invece di indicare un dato sbagliato. Se vuoi,
  in un secondo passaggio ispezioniamo l'HTML reale della pagina per
  affinare questo punto.
- **Promo Racing**: il prezzo non è mostrato nella pagina calendario, solo
  nella pagina di dettaglio del singolo evento — per ora resta vuoto.
  Si può aggiungere una seconda richiesta HTTP alla pagina di dettaglio se
  serve, ma rallenta un po' l'aggiornamento (8 eventi extra = 8 richieste
  in più per ogni ciclo).
- Se un sito cambia layout, il relativo scraper può smettere di trovare
  eventi. `main.py` isola gli errori: se uno scraper fallisce, gli altri
  continuano a funzionare, e l'elenco `sources_failed` in `data.json`
  (visibile anche in fondo alla pagina del sito) segnala quale agenzia
  non è stata raggiunta correttamente nell'ultimo giro.
