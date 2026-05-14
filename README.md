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

### Uruchomienie całego systemu
Aby zbudować obrazy i uruchomić wszystkie moduły (Baza danych, Scraper, Backend, Frontend), wykonaj poniższą komendę w folderze głównym:

```bash
docker-compose up --build

