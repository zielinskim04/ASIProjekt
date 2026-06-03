# Frontend

Aplikacja webowa do przeglądania ofert nieruchomości na mapie Warszawy — zbudowana w **React 18** z mapą **Leaflet** i serwowana przez **nginx**.

## Wymagania systemowe

- Node.js 18+
- npm 9+
- Działający backend (`http://localhost:8000`)

## Instalacja

```bash
cd frontend
npm install
```

## Uruchomienie

### Lokalnie (tryb deweloperski)

```bash
npm start
```

Aplikacja dostępna pod: `http://localhost:3000`

W trybie deweloperskim zapytania do `/api/` są proksy-owane na `http://backend:8000` (ustawione w `package.json` → `"proxy"`).

### Docker (produkcyjny)

```bash
docker compose up frontend --build
```

Aplikacja jest budowana (`npm run build`) do statycznych plików, które nginx serwuje na porcie `80`.

## Architektura

### Struktura komponentów

Aplikacja jest zbudowana jako **pojedynczy komponent** `App` (`src/App.js`) zarządzający całym stanem przez hooki React.

```
App
├── <header>          — pasek górny: tytuł + statystyki bazy (liczba ofert, POI, data)
├── .layout
│   ├── <aside.sidebar>  — panel filtrów
│   │   ├── select POI category
│   │   ├── input[range] POI radius (widoczny warunkowo)
│   │   ├── input cena min/max
│   │   ├── input cena/m² max
│   │   ├── input powierzchnia min/max
│   │   └── input pokoje min/max
│   └── <MapContainer>   — mapa Leaflet z markerami
│       └── <Marker> → <Popup>  — popup z detalami i przyciskiem "Infrastruktura"
└── .overlay (modal)  — panel POI dla wybranej nieruchomości
```

### Zarządzanie stanem

Cały stan aplikacji żyje w `App` przez `useState`:

| Stan | Typ | Opis |
|------|-----|------|
| `properties` | `array` | Lista nieruchomości wyświetlana na mapie |
| `filters` | `object` | Wartości wszystkich pól filtrów |
| `status` | `object` | Statystyki bazy (z `/api/v1/ingestion/status`) |
| `selectedProp` | `object\|null` | Nieruchomość otwarta w panelu POI |
| `loading` / `poiLoading` | `bool` | Flagi ładowania |
| `error` | `string\|null` | Komunikat błędu |

Dane są pobierane przez `fetch` — brak zewnętrznej biblioteki do zarządzania stanem.

### Przepływ danych

```
Uruchomienie
  └─► GET /api/v1/ingestion/status  →  status (liczba ofert, POI, data)
  └─► GET /api/v1/properties?limit=300  →  początkowa lista

Kliknięcie "Szukaj"
  └─► GET /api/v1/properties?<filtry>  →  odświeżona lista markerów

Kliknięcie "Infrastruktura" w popupie
  └─► GET /api/v1/properties/{id}  →  szczegóły + lista 20 najbliższych POI
```

### Routing i proxy (nginx)

W produkcji nginx (`nginx.conf`) obsługuje dwa typy żądań:

- `/api/*` — proxy do backendu FastAPI (`http://backend:8000`)
- `/*` — serwuje statyczny build React (`/index.html` dla client-side routing)

### Główne zależności

| Pakiet | Wersja | Rola |
|--------|--------|------|
| `react` / `react-dom` | 18.2 | Biblioteka UI |
| `react-leaflet` | 4.2 | Komponent mapy dla React |
| `leaflet` | 1.9 | Silnik mapy (OpenStreetMap) |
| `react-scripts` | 5.0 | Build toolchain (CRA) |

## Pliki

| Plik | Opis |
|------|------|
| `src/App.js` | Jedyny komponent — cała logika aplikacji |
| `src/App.css` | Style (layout flex, sidebar, mapa, popup, modal POI) |
| `src/index.js` | Punkt wejścia React |
| `public/index.html` | Szablon HTML |
| `nginx.conf` | Konfiguracja serwera produkcyjnego |
| `Dockerfile.prod` | Obraz produkcyjny (build + nginx) |
