# Data Downloader

Moduł do pobierania, geokodowania i zapisywania ofert nieruchomości z portalu **adresowo.pl** do bazy PostgreSQL.

## Wymagania systemowe

- Python 3.9+
- PostgreSQL 13+ z rozszerzeniem PostGIS
- Internet (dla API geokodowania i scrapingu)

## Instalacja

### 1. Klonuj repozytorium i wejdź do katalogu

```bash
cd data_downloader
```

### 2. Utwórz wirtualne środowisko (opcjonalne, ale zalecane)

```bash
python -m venv venv
```

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Zainstaluj pakiet z zależnościami

```bash
python -m pip install -e .
```

Lub z dodatkowymi narzędziami:

```bash
python -m pip install -e ".[dev]"     # dev tools (pytest, black, flake8)
python -m pip install -e ".[geo]"     # geo tools (geopy, folium)
python -m pip install -e ".[all]"     # wszystkie dodatki
```

## Konfiguracja

### 1. Ustaw zmienne środowiska w `.env`

Plik `.env` już istnieje z domyślnymi wartościami:

```env
DB_NAME=realestate
DB_USER=admin
DB_PASSWORD=admin
DB_HOST=localhost
DB_PORT=5432
```

**Dla Docker:**
```env
DB_HOST=db
```

### 2. Upewnij się, że PostgreSQL/Docker jest uruchomiony

```bash
# Sprawdź połączenie
psql -h localhost -U admin -d realestate -c "SELECT 1;"
```

Lub dla Docker:
```bash
docker compose up -d db
```

## Uruchomienie

### Pobierz i przetwórz dane

```bash
cd src
python main.py
```

### Czego oczekiwać

1. **Scraping** — pobiera ~40 ofert z adresowo.pl
2. **Filtracja** — wybiera oferty z wybranych dzielnic (Mokotów, Ochota, Rembertów)
3. **Geokodowanie** — konwertuje adresy na współrzędne (opóźnienie 1.2s między zapytaniami)
4. **Zapis do bazy** — wstawia dane do tabeli `properties` w bazie `realestate`

### Przykładowy wynik

```
2026-05-14 20:47:54 [INFO] Rozpoczynam potok danych...
2026-05-14 20:47:54 [INFO] Rozpoczynam pobieranie ofert z adresowo.pl...
2026-05-14 20:47:55 [INFO] Zescrapowano 40 ofert.
2026-05-14 20:47:55 [INFO] Po filtracji dzielnic zostało ofert: 7
2026-05-14 20:48:24 [INFO] Udało się przetworzyć 5 ofert.
2026-05-14 20:48:24 [INFO] Zapisano 5 nowych ofert do bazy PostgreSQL.
```

## Baza danych

### Tabela `properties`

Kolumny przechowywane w bazie:
- `id` — ID oferty
- `title` — Tytuł oferty
- `address_clean` — Czysty adres
- `price` — Cena (numeric)
- `area` — Metraż (numeric)
- `rooms` — Liczba pokoi (integer)
- `geom` — Współrzędne (PostGIS Point, SRID 4326)
- `link` — URL oferty (unique)
- `scraped_at` — Data pobrania (timestamp)
