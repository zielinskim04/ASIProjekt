# ASIProjekt — Property Location Analyzer

System do analizy ofert nieruchomości pod kątem bliskości punktów POI (przystanki, kultura, usługi).

## Architektura (Model C4)
[Diagram architektury](https://viewer.diagrams.net/?tags=%7B%7D&lightbox=1&highlight=0000ff&edit=_blank&layers=1&nav=1&title=ASIProjekt&dark=auto#Uhttps%3A%2F%2Fdrive.google.com%2Fuc%3Fid%3D1kvtrY5iuOh5Ky-eKvw5kUD4Uj-lJ5v1e%26export%3Ddownload)

## Stack Technologiczny
| Warstwa | Technologia |
|---|---|
| Frontend | React (mapy + filtrowanie) |
| Backend | Python, FastAPI |
| Scraper | Python, BeautifulSoup |
| Baza danych | PostgreSQL + PostGIS |
| Integracje | Nominatim API, Overpass API (OpenStreetMap) |

## Struktura projektu

```
ASIProjekt/
├── backend/                  # FastAPI — serwer API
│   ├── src/
│   │   ├── main.py           # definicje endpointów
│   │   └── database.py       # zapytania do bazy danych
│   ├── tests/                # testy jednostkowe i API
│   ├── performance_tests/    # testy wydajnościowe (Locust)
│   ├── Dockerfile.dev
│   └── Dockerfile.prod
│
├── data_downloader/          # scraper + geokodowanie + pobieranie POI
│   ├── src/
│   │   ├── main.py
│   │   ├── scraper.py        # scraping adresowo.pl
│   │   ├── parser.py
│   │   ├── geocoder.py       # Nominatim API
│   │   └── database.py       # zapis do bazy
│   ├── tests/
│   ├── Dockerfile.dev
│   └── Dockerfile.prod
│
├── frontend/                 # React UI
│   └── Dockerfile.prod
│
├── database/
│   └── init.sql              # schemat bazy danych
│
├── docker-compose.yml        # baza wspólna dla wszystkich środowisk
├── docker-compose.dev.yml    # środowisko deweloperskie
├── docker-compose.test.yml   # środowisko testowe
├── docker-compose.prod.yml   # środowisko produkcyjne
└── docker-compose.perf.yml   # testy wydajnościowe (Locust UI)
```

## API Endpoints

| Metoda | Endpoint | Opis |
|---|---|---|
| GET | `/api/v1/properties` | Lista mieszkań pasujących do filtrów |
| GET | `/api/v1/properties/{id}` | Detale oferty + najbliższe punkty POI |
| GET | `/api/v1/ingestion/status` | Status ostatniego scrapowania danych |

### Filtry dla `GET /api/v1/properties`

| Parametr | Typ | Domyślnie | Opis |
|---|---|---|---|
| `price_min` / `price_max` | float | — | Zakres ceny (PLN) |
| `area_min` / `area_max` | float | — | Zakres powierzchni (m²) |
| `rooms_min` / `rooms_max` | int | — | Liczba pokoi |
| `price_per_sqm_max` | float | — | Max cena za m² |
| `poi_category` | string | — | Kategoria POI (np. `bus_stop`, `school`) |
| `poi_radius_m` | int | 500 | Promień szukania POI w metrach (50–5000) |
| `limit` | int | 300 | Maks. liczba wyników (1–1000) |

### Dokumentacja interaktywna (Swagger)

Po uruchomieniu backendu dokumentacja API jest dostępna automatycznie:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Schemat OpenAPI (JSON):** http://localhost:8000/openapi.json

## Uruchomienie

System jest w pełni skonteneryzowany. Wymagania: **Docker** i **Docker Compose**.

### Środowisko Deweloperskie (DEV)

Hot-reload kodu bez potrzeby przebudowywania obrazów.

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

| Usługa | Adres |
|---|---|
| Backend API + Swagger | http://localhost:8000/docs |
| Frontend (React) | http://localhost:3000 |
| Baza danych (PostgreSQL) | localhost:5432 |

### Środowisko Testowe (TEST)

Uruchamia `pytest` na sterylnej bazie (`realestate_test`) i wyłącza kontenery po zakończeniu.

```bash
docker compose -f docker-compose.yml -f docker-compose.test.yml up --build --abort-on-container-exit
```

#### Uruchomienie testów lokalnie (bez Dockera)

```bash
cd backend
pip install -e ".[dev]"
pytest tests/ -v
```

### Środowisko Produkcyjne (PROD)

Kod skopiowany do obrazów, frontend serwowany przez Nginx.

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

| Usługa | Adres |
|---|---|
| Frontend | http://localhost:80 |
| Backend API | http://localhost:8000 |

Logi scrapera:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f data_downloader
```

### Testy wydajnościowe (Locust)

1. Uruchom środowisko produkcyjne (patrz wyżej)
2. Uruchom Locust:

```bash
docker compose -f docker-compose.perf.yml up
```

3. Panel Locust: http://localhost:8089
