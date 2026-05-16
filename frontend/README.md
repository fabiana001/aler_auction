# Frontend — ALER Auction Map

Applicazione **React + Vite** che visualizza le aste immobiliari su una mappa **Leaflet** interattiva.

## Avvio

```bash
# Installa dipendenze (solo la prima volta)
npm install

# Sviluppo (con HMR)
npm run dev

# Build di produzione
npm run build

# Preview build di produzione
npm run preview
```

L'applicazione sarà disponibile su **http://localhost:5173**

## Struttura Codice

```
frontend/
├── src/
│   ├── main.jsx                    ← Entry point — monta React su #root
│   ├── App.jsx                     ← Layout: header + mappa
│   ├── App.css                     ← Stili App
│   ├── index.css                   ← Stili globali
│   ├── components/
│   │   ├── MapContainer.jsx        ← Mappa Leaflet con marker
│   │   └── AuctionPopup.jsx        ← Popup informativo per ogni marker
│   ├── hooks/
│   │   └── useAuctions.js          ← Hook: fetch + stato aste
│   └── utils/
│       └── api.js                  ← Client axios per il backend
├── public/
│   └── favicon.svg
├── index.html                      ← HTML base
├── vite.config.js                  ← Configurazione Vite
├── package.json
└── .env                            ← VITE_BACKEND_URL
```

## Componenti

### `App.jsx`

Layout principale dell'applicazione. Contiene:
- **Header** con titolo "🗺️ Aste Immobiliari ALER — Milano" e contatore aste
- **Loader** visualizzato durante il caricamento
- **Banner errore** in caso di fallimento
- **`<AuctionMap />`** — la mappa a schermo pieno

### `MapContainer.jsx`

Componente mappa Leaflet. Responsabilità:
- Inizializza la mappa centrata su Milano (45.4642, 9.19) con zoom 12
- Aggiunge tile layer OpenStreetMap
- Renderizza un **`<Marker />`** per ogni asta con icona default
- Ogni marker contiene un **`<AuctionPopup />`**
- **`FitBounds`** — componente interno che auto-adatta la vista ai marker

### `AuctionPopup.jsx`

Popup mostrato al click su un marker. Visualizza:
- **Indirizzo** (titolo)
- **Tipologia** immobile
- **Prezzo base** (formattato in €)
- **Offerta finale** (se disponibile)
- **Vani**, **Superficie**, **€/m²** (se disponibili)
- **Esito** asta, **Data asta** (se disponibili)

### `useAuctions.js`

Hook personalizzato che gestisce:
- `auctions` — array delle aste caricate
- `total` — numero totale di aste
- `loading` — stato di caricamento
- `error` — messaggio di errore
- `reload()` — funzione per ricaricare i dati

### `api.js`

Client axios configurato con:
- `baseURL` → `${VITE_BACKEND_URL}/api`
- `timeout` → 10 secondi
- `fetchAuctions(params)` — GET /auctions
- `fetchAuction(id)` — GET /auctions/{id}

## Configurazione

File `frontend/.env`:

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `VITE_BACKEND_URL` | `http://localhost:8000` | URL del backend API |

> **Nota**: le variabili d'ambiente nel frontend devono iniziare con `VITE_` per essere incluse nel build (convensione Vite).

## Dipendenze

| Pacchetto | Versione | Scopo |
|-----------|----------|-------|
| react | 19 | UI framework |
| react-dom | 19 | Rendering DOM |
| leaflet | 1.9.4 | Libreria mappa |
| react-leaflet | 5.0.0 | Componenti React per Leaflet |
| axios | ≥ 1.16 | Client HTTP |
| vite | 8 | Build tool + dev server |

## Build di Produzione

```bash
npm run build
```

Output in `dist/`:
- `index.html` (0.45 kB)
- `assets/index-*.css` (15 kB, Leaflet CSS incluso)
- `assets/index-*.js` (390 kB, bundle completo)

Per servire la build:

```bash
npm run preview    # Avvia server su localhost:4173
```

Oppure servire con qualsiasi static file server:

```bash
npx serve dist/
```
