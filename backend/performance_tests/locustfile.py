from locust import HttpUser, task, between
import random

class RealEstateAPIUser(HttpUser):
    wait_time = between(1, 3)

    @task(1)
    def view_properties_list(self):
        """
        Symuluje użytkownika przeglądającego listę nieruchomości z losowymi filtrami.
        Waga (3) oznacza, że to zadanie będzie wykonywane 3 razy częściej niż inne.
        """
        price_min = 400000
        price_max = price_min + 300000

        self.client.get(f"/api/v1/properties?price_min={price_min}&price_max={price_max}&limit=50")

    @task(1)
    def view_properties_filtered_by_poi(self):
        """
        Scenariusz 2: Szukanie ofert blisko wybranego POI (BARDZO CIĘŻKIE).
        To wywoła zapytanie ST_DWithin na całej tabeli.
        """
        chosen_category = "school"

        radius = 500

        self.client.get(f"/api/v1/properties?poi_category={chosen_category}&poi_radius_m={radius}&limit=50")

    @task(2)
    def view_property_details_with_pois(self):
        """
        Symuluje użytkownika wchodzącego w detale oferty, co odpala ciężkie 
        zapytanie przestrzenne (PostGIS ST_DWithin) w celu znalezienia POI.
        """
        property_id = 1
        with self.client.get(f"/api/v1/properties/{property_id}", catch_response=True) as response:
            if response.status_code == 404:
                response.success()