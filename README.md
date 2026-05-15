# ASIProjekt


#  Property Location Analyzer

System do analizy ofert nieruchomości pod kątem bliskości punktów POI (przystanki, kultura, usługi).

##  Architektura (Model C4)
[Diagram architektury](https://viewer.diagrams.net/?tags=%7B%7D&lightbox=1&highlight=0000ff&edit=_blank&layers=1&nav=1&title=ASIProjekt&dark=auto#Uhttps%3A%2F%2Fdrive.google.com%2Fuc%3Fid%3D1kvtrY5iuOh5Ky-eKvw5kUD4Uj-lJ5v1e%26export%3Ddownload)

##  Stack Technologiczny
* **Frontend:** React (Mapy + Filtrowanie)
* **Backend:** Python (FastAPI)
* **Scraper:** Python (BeautifulSoup)
* **Baza danych:** PostgreSQL + PostGIS (dane przestrzenne)
* **Integracje:** Nominatim API, Overpass API (OpenStreetMap)

## 📡 API Endpoints
* `GET /api/v1/properties` – lista mieszkań pasujących do filtrów.
* `GET /api/v1/properties/{id}` – detale oferty + lista najbliższych punktów POI.
* `GET /api/v1/ingestion/status` – status ostatniego scrapowania danych.

## ⚙️ Kluczowe Komponenty
1. **Data Downloader:** Automatyczny scraper ofert z `adresowo.pl`, normalizacja adresów do współrzędnych ($Lat, Lng$) i pobieranie POI z OpenStreetMap.
2. **APP API:** Silnik wyszukiwania wykorzystujący PostGIS do obliczeń odległości w czasie rzeczywistym.
3. **APP UI:** Interfejs użytkownika prezentujący atrakcyjność lokalizacji na mapie.

## 🚀 Instrukcja uruchomienia

System jest w pełni skonteneryzowany, co zapewnia powtarzalność środowiska (dev, test, prod) zgodnie z wymaganiami projektu.

### Wymagania
- Docker
- Docker Compose

### 💻 Środowisko Deweloperskie (DEV)
Służy do codziennej pracy. Posiada włączone przeładowywanie kodu w locie (Hot-Reload) za pomocą wolumenów Dockera. Porty są otwarte na hoście, co ułatwia debugowanie.

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```
Backend API (Swagger): http://localhost:8000/docs

Frontend (React): http://localhost:3000

Baza danych (PostgreSQL): localhost:5432

### 🧪 Środowisko Testowe (TEST)
Służy do automatycznego testowania systemu na sterylnej bazie danych (realestate_test), aby nie zanieczyścić danych deweloperskich. Uruchamia pytest i po zakończeniu automatycznie wyłącza kontenery.

```bash
docker compose -f docker-compose.yml -f docker-compose.test.yml up --build --abort-on-container-exit
```

### 🌍 Środowisko Produkcyjne (PROD)
Zoptymalizowane, "zamrożone" środowisko gotowe do wdrożenia na serwer (kod skopiowany na stałe do wnętrza obrazów, frontend serwowany przez ultraszybki serwer Nginx).

``` bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```
Frontend: http://localhost:80 (domyślny port HTTP)

Backend API: http://localhost:8000

To see logs:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f data_downloader
```



