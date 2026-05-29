# Raport z testów wydajnościowych (Performance Tests)

## 1. Środowisko testowe i scenariusze użytkowników

Środowisko zostało zaprojektowane tak, aby symulować realistyczne zachowanie użytkowników w aplikacji. Profil obciążenia opiera się na następujących założeniach:

* **Proporcje ruchu (Kliknięcia vs. Filtry):** Skrypt testowy symuluje zachowanie, w którym **użytkownik dwa razy częściej klika w szczegóły konkretnej oferty** (`GET /api/v1/properties/1`), niż korzysta z opcji filtrowania wyników. Odzwierciedla to typowy ruch na portalach ogłoszeniowych (więcej czasu spędzanego na przeglądaniu niż na wyszukiwaniu).
* **Rodzaje wykorzystywanych filtrów:** W testach uwzględniono dwa skrajnie różne rodzaje zapytań filtrujących, co pozwala ocenić wydajność bazy danych:
    * **Filtr lekki (cenowy):** Wykorzystuje parametry `price_min` oraz `price_max`. Jest to standardowe, proste zapytanie bazodanowe po indeksowanych polach numerycznych, które wykonuje się relatywnie szybko.
    * **Filtr ciężki (geoprzestrzenny):** Wykorzystuje parametry `poi_category` (np. *school*) oraz `poi_radius_m`. Jest to zapytanie **znacznie cięższe**, ponieważ pod spodem wykonuje złożone obliczenia geograficzne i złączenia przestrzenne (Spatial Joins), wyliczając odległości obiektów w locie. To ten endpoint odpowiada za największe opóźnienia w systemie.

Najważniejszą informacją płynącą z testów jest **całkowity brak błędów (0% Fails)** we wszystkich scenariuszach. System, nawet pod dużym obciążeniem, nie odrzuca połączeń i nie zwraca błędów typu 5xx, a jedynie proporcjonalnie wydłuża czas odpowiedzi.

---

## 2. Wyniki testów

### Scenariusz A: Niskie obciążenie (10 użytkowników, ramp-up 2)
Typowy, spokojny ruch w serwisie. Zapytania obsługiwane są płynnie, a opóźnienia są minimalne, z wyjątkiem ciężkiego filtru geograficznego, który już na tym etapie wykazuje większą złożoność obliczeniową.

| Typ zapytania | Requests | Fails | Median | Average |
| :--- | :--- | :--- | :--- | :--- |
| **Pobranie oferty** (`/properties/1`) | ~196 | **0** | < 10 ms | **~ 17 ms** |
| **Lekki filtr** (`price_min`, `price_max`) | ~62 | **0** | ~ 28 ms | **~ 28 ms** |
| **Ciężki filtr POI** (`poi_category`, `radius`) | ~52 | **0** | ~ 860 ms | **~ 876 ms** |

---

### Scenariusz B: Średnie obciążenie (50 użytkowników, ramp-up 10)
Standardowy ruch w godzinach szczytu. Zgodnie z założeniami widzimy, że liczba pobrań oferty (1042) jest w przybliżeniu równa sumie wywołań obu filtrów (563 + 523), co potwierdza stosunek 2:1.

| Typ zapytania | Requests | Fails | Median | Average |
| :--- | :--- | :--- | :--- | :--- |
| **Pobranie oferty** (`/properties/1`) | 1042 | **0** | 420 ms | **435 ms** |
| **Lekki filtr** (`price_min`, `price_max`) | 563 | **0** | 560 ms | **537 ms** |
| **Ciężki filtr POI** (`poi_category`, `radius`) | 523 | **0** | 1200 ms | **1180 ms** |

---

### Scenariusz C: Wysokie obciążenie (100 użytkowników, ramp-up 50)
Sytuacja nagłego skoku popularności (tzw. efekt "wykopu") – np. w portalach społecznościowych pojawił się link i wiele osób weszło w niego niemal równocześnie.

| Typ zapytania | Requests | Fails | Median | Average |
| :--- | :--- | :--- | :--- | :--- |
| **Pobranie oferty** (`/properties/1`) | 537 | **0** | 2200 ms | **2169 ms** |
| **Lekki filtr** (`price_min`, `price_max`) | 240 | **0** | 860 ms | **839 ms** |
| **Ciężki filtr POI** (`poi_category`, `radius`) | 238 | **0** | 4900 ms | **4871 ms** |

---

## 3. Podsumowanie i wnioski

1. **Stabilność aplikacji (Brak Faili):** Niezależnie od poziomu obciążenia, system wykazał się 100% niezawodnością pod kątem dostarczania odpowiedzi. Brak jakichkolwiek błędów (0 Fails) świadczy o prawidłowej konfiguracji serwera i bazy danych (połączenia nie są zrywane, system się nie dławi).
2. **Wąskie gardło (Złączenia geoprzestrzenne):** Filtr bazujący na sprawdzaniu promienia dla punktów POI jest najdroższym zapytaniem w systemie. Podczas nagłego skoku ruchu (100 użytkowników), średni czas odpowiedzi dla tego endpointu wynosi niemal **4.9 sekundy**. Operacje GIS są złożone obliczeniowo.
3. **Płynna degradacja wydajności (Graceful Degradation):** Wraz ze wzrostem ruchu z 10 do 100 użytkowników, czasy odpowiedzi rosną liniowo dla wszystkich zapytań (np. pobranie oferty rośnie z ~17 ms do ~2169 ms). Serwer kolejkuje zapytania i odpowiada na nie z opóźnieniem, zamiast całkowicie odmawiać usługi.