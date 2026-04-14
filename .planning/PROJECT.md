# Aler Auction — Piattaforma Web Aste Immobiliari Milano

## What This Is

Piattaforma web per investitori privati che trasforma la pipeline di analisi aste giudiziarie di Milano in un'interfaccia interattiva. Mostra tutte le aste su mappa, permette di esplorare trend di prezzo per via/zona, e fornisce un'analisi AI del valore di mercato del quartiere confrontando ogni immobile all'asta con i prezzi reali da portali immobiliari.

## Core Value

Un investitore deve poter valutare in pochi secondi se un'asta è un'opportunità reale rispetto al mercato, senza dover fare ricerche manuali su più siti.

## Requirements

### Validated

- ✓ Estrazione dati da PDF aste giudiziarie — existing pipeline
- ✓ Geocoding indirizzi via Google Maps API — existing pipeline
- ✓ Clustering spaziale e analisi prezzi (HDBSCAN) — existing pipeline
- ✓ Dataset consolidato con lat/lng e metriche prezzo — existing data layer

### Active

- [ ] Mappa interattiva con pin di tutte le aste e info principali (indirizzo, prezzo base, tipologia)
- [ ] Ricerca per via/indirizzo con visualizzazione trend prezzi nel raggio configurabile (default 500m)
- [ ] Analisi AI del valore di mercato del quartiere: top 50 immobili simili da portali immobiliari (immobiliare.it / casa.it) con stima valore medio al m²
- [ ] Confronto asta vs mercato: calcolo % di sconto rispetto al prezzo di mercato stimato
- [ ] API REST FastAPI che espone i dati del dataset processato
- [ ] Frontend React con mappa (Leaflet/MapLibre) e UI per ricerche e analisi

### Out of Scope

- Login / autenticazione utenti — piattaforma completamente pubblica per v1
- Upload PDF da parte dell'utente — i dati arrivano dalla pipeline esistente
- Copertura geografica oltre Milano — focus su aste milanesi per v1
- Notifiche / alert aste nuove — funzione futura
- Storico prezzi e serie temporali — richiede dati multi-periodo non ancora disponibili

## Context

**Codebase esistente:** Pipeline Python (Python 3.14+, uv) con 8 stage sequenziali che producono `data/consolidated_auction_dataset_analyzed.csv` — il punto di partenza per la piattaforma web. La pipeline gira manualmente via script CLI, non è un server.

**Stack attuale:** Python puro (pandas, pdfplumber, hdbscan, googlemaps, beautifulsoup4). Nessun web framework installato.

**Dati prodotti:** Ogni asta ha indirizzo, lat/lng, prezzo base, categoria, metriche di clustering spaziale e stima prezzo al m² da analisi HDBSCAN.

**Portale fonte aste:** alermilanopianovendite.it (aste giudiziarie Milano, recuperate via Wayback Machine).

**Portali per analisi mercato:** immobiliare.it e casa.it (scraping o API per trovare i 50 immobili simili per tipo, zona, superficie).

## Constraints

- **Tech Stack**: FastAPI (backend) + React + Leaflet (frontend) — stack moderno adatto a mappa interattiva e analisi AI
- **Python version**: >=3.14 (già imposto da pyproject.toml)
- **Package Manager**: uv (già in uso nel progetto)
- **Dati**: Il dataset analizzato è il punto di input — nessuna modifica alla pipeline esistente in v1
- **Geografica**: Solo aste Milano per v1
- **Scraping**: Il web scraping dei portali immobiliari deve rispettare rate limits e robots.txt; considerare caching aggressivo dei risultati

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| FastAPI + React | API Python consistente col codebase, React per UI mappa ricca | — Pending |
| Leaflet/MapLibre per mappa | Open source, ottimo supporto React, nessun costo API mappa | — Pending |
| immobiliare.it + casa.it per analisi mercato | Maggiore copertura Milano, dati strutturati, scraping fattibile | — Pending |
| Nessun auth in v1 | Piattaforma pubblica, riduce complessità iniziale | — Pending |
| Dati serviti da CSV analizzato | Riusa la pipeline esistente senza modifiche, prototipo rapido | — Pending |

## Evolution

Questo documento evolve ad ogni transizione di fase e milestone.

**Dopo ogni fase** (via `/gsd-transition`):
1. Requirements invalidati? → Sposta in Out of Scope con motivo
2. Requirements validati? → Sposta in Validated con riferimento fase
3. Nuovi requirements emersi? → Aggiungi in Active
4. Decisioni da registrare? → Aggiungi in Key Decisions
5. "What This Is" ancora accurato? → Aggiorna se deriva

**Dopo ogni milestone** (via `/gsd-complete-milestone`):
1. Review completa di tutte le sezioni
2. Core Value check — ancora la priorità giusta?
3. Audit Out of Scope — i motivi sono ancora validi?
4. Aggiorna Context con stato corrente

---
*Last updated: 2026-04-14 after initialization*
