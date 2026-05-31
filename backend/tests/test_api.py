import pytest
from unittest.mock import patch
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)

MODULE = "src.main"

# Przykładowe dane używane w wielu testach
SAMPLE_PROPERTY = {
    "id": 1,
    "title": "Warszawa, Mokotów - ul. Puławska 10",
    "address_clean": "ul. Puławska 10, Warszawa",
    "price": 650_000.0,
    "area": 50.0,
    "rooms": 2,
    "link": "https://adresowo.pl/oferta/1",
    "scraped_at": "2026-05-29T06:00:00",
    "lat": 52.19,
    "lon": 21.02,
    "price_per_sqm": 13_000,
}

SAMPLE_PROPERTY_WITH_POIS = {
    **SAMPLE_PROPERTY,
    "nearest_pois": [
        {"id": 10, "category": "bus_stop", "name": "Puławska",
         "lat": 52.191, "lon": 21.021, "distance_m": 80},
        {"id": 11, "category": "school", "name": "SP nr 5",
         "lat": 52.195, "lon": 21.025, "distance_m": 350},
    ],
}

SAMPLE_STATUS = {
    "last_scraped_at": "2026-05-29T06:00:00",
    "total_properties": 120,
    "total_pois": 9200,
    "poi_categories": {
        "bus_stop": 3500,
        "school": 400,
        "restaurant": 1200,
    },
}


# ── GET /api/v1/properties ────────────────────────────────────────────────────

class TestGetProperties:

    @patch(f"{MODULE}.query_properties", return_value=[SAMPLE_PROPERTY])
    def test_returns_200_with_list(self, mock_query):
        response = client.get("/api/v1/properties")

        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) == 1

    @patch(f"{MODULE}.query_properties", return_value=[SAMPLE_PROPERTY])
    def test_response_contains_expected_fields(self, mock_query):
        response = client.get("/api/v1/properties")

        prop = response.json()[0]
        assert "id" in prop
        assert "price" in prop
        assert "area" in prop
        assert "lat" in prop
        assert "lon" in prop
        assert "price_per_sqm" in prop

    @patch(f"{MODULE}.query_properties", return_value=[])
    def test_empty_result_returns_empty_list(self, mock_query):
        response = client.get("/api/v1/properties")

        assert response.status_code == 200
        assert response.json() == []

    @patch(f"{MODULE}.query_properties", return_value=[SAMPLE_PROPERTY])
    def test_price_filters_passed_to_query(self, mock_query):
        client.get("/api/v1/properties?price_min=300000&price_max=700000")

        mock_query.assert_called_once_with(
            price_min=300_000.0,
            price_max=700_000.0,
            area_min=None,
            area_max=None,
            rooms_min=None,
            rooms_max=None,
            price_per_sqm_max=None,
            poi_category=None,
            poi_radius_m=500,
            limit=300,
        )

    @patch(f"{MODULE}.query_properties", return_value=[])
    def test_poi_filters_passed_to_query(self, mock_query):
        client.get("/api/v1/properties?poi_category=bus_stop&poi_radius_m=1000")

        call_kwargs = mock_query.call_args[1]
        assert call_kwargs["poi_category"] == "bus_stop"
        assert call_kwargs["poi_radius_m"] == 1000

    @patch(f"{MODULE}.query_properties", return_value=[])
    def test_all_filters_passed_to_query(self, mock_query):
        client.get(
            "/api/v1/properties"
            "?price_min=200000&price_max=800000"
            "&area_min=35&area_max=100"
            "&rooms_min=1&rooms_max=4"
            "&price_per_sqm_max=15000"
            "&poi_category=school&poi_radius_m=750"
            "&limit=50"
        )

        call_kwargs = mock_query.call_args[1]
        assert call_kwargs["price_min"] == 200_000.0
        assert call_kwargs["price_max"] == 800_000.0
        assert call_kwargs["area_min"] == 35.0
        assert call_kwargs["area_max"] == 100.0
        assert call_kwargs["rooms_min"] == 1
        assert call_kwargs["rooms_max"] == 4
        assert call_kwargs["price_per_sqm_max"] == 15_000.0
        assert call_kwargs["poi_category"] == "school"
        assert call_kwargs["poi_radius_m"] == 750
        assert call_kwargs["limit"] == 50

    def test_poi_radius_below_minimum_returns_422(self):
        response = client.get("/api/v1/properties?poi_radius_m=10")
        assert response.status_code == 422

    def test_poi_radius_above_maximum_returns_422(self):
        response = client.get("/api/v1/properties?poi_radius_m=9999")
        assert response.status_code == 422

    def test_limit_above_maximum_returns_422(self):
        response = client.get("/api/v1/properties?limit=9999")
        assert response.status_code == 422

    def test_limit_zero_returns_422(self):
        response = client.get("/api/v1/properties?limit=0")
        assert response.status_code == 422

    @patch(f"{MODULE}.query_properties",
           side_effect=HTTPException(status_code=503, detail="Błąd bazy danych: timeout"))
    def test_db_error_returns_503(self, mock_query):
        response = client.get("/api/v1/properties")

        assert response.status_code == 503
        assert "Błąd bazy danych" in response.json()["detail"]


# ── GET /api/v1/properties/{property_id} ─────────────────────────────────────

class TestGetPropertyById:

    @patch(f"{MODULE}.query_property_with_pois", return_value=SAMPLE_PROPERTY_WITH_POIS)
    def test_returns_200_with_property(self, mock_query):
        response = client.get("/api/v1/properties/1")

        assert response.status_code == 200
        assert response.json()["id"] == 1

    @patch(f"{MODULE}.query_property_with_pois", return_value=SAMPLE_PROPERTY_WITH_POIS)
    def test_response_contains_nearest_pois(self, mock_query):
        response = client.get("/api/v1/properties/1")

        data = response.json()
        assert "nearest_pois" in data
        assert isinstance(data["nearest_pois"], list)
        assert len(data["nearest_pois"]) == 2

    @patch(f"{MODULE}.query_property_with_pois", return_value=SAMPLE_PROPERTY_WITH_POIS)
    def test_poi_contains_distance_and_category(self, mock_query):
        response = client.get("/api/v1/properties/1")

        poi = response.json()["nearest_pois"][0]
        assert "category" in poi
        assert "distance_m" in poi
        assert "name" in poi

    @patch(f"{MODULE}.query_property_with_pois", return_value=SAMPLE_PROPERTY_WITH_POIS)
    def test_correct_id_passed_to_query(self, mock_query):
        client.get("/api/v1/properties/42")

        mock_query.assert_called_once_with(42)

    @patch(f"{MODULE}.query_property_with_pois",
           side_effect=HTTPException(status_code=404, detail="Nieruchomość nie znaleziona"))
    def test_nonexistent_property_returns_404(self, mock_query):
        response = client.get("/api/v1/properties/999")

        assert response.status_code == 404
        assert "nie znaleziona" in response.json()["detail"]

    def test_non_integer_id_returns_422(self):
        response = client.get("/api/v1/properties/abc")
        assert response.status_code == 422

    @patch(f"{MODULE}.query_property_with_pois",
           side_effect=HTTPException(status_code=503, detail="Błąd bazy danych: timeout"))
    def test_db_error_returns_503(self, mock_query):
        response = client.get("/api/v1/properties/1")

        assert response.status_code == 503


# ── GET /api/v1/ingestion/status ─────────────────────────────────────────────

class TestGetIngestionStatus:

    @patch(f"{MODULE}.query_ingestion_status", return_value=SAMPLE_STATUS)
    def test_returns_200(self, mock_query):
        response = client.get("/api/v1/ingestion/status")

        assert response.status_code == 200

    @patch(f"{MODULE}.query_ingestion_status", return_value=SAMPLE_STATUS)
    def test_response_contains_all_required_fields(self, mock_query):
        response = client.get("/api/v1/ingestion/status")

        data = response.json()
        assert "last_scraped_at" in data
        assert "total_properties" in data
        assert "total_pois" in data
        assert "poi_categories" in data

    @patch(f"{MODULE}.query_ingestion_status", return_value=SAMPLE_STATUS)
    def test_poi_categories_is_dict(self, mock_query):
        response = client.get("/api/v1/ingestion/status")

        assert isinstance(response.json()["poi_categories"], dict)

    @patch(f"{MODULE}.query_ingestion_status", return_value=SAMPLE_STATUS)
    def test_counts_match_expected_values(self, mock_query):
        response = client.get("/api/v1/ingestion/status")

        data = response.json()
        assert data["total_properties"] == 120
        assert data["total_pois"] == 9200

    @patch(f"{MODULE}.query_ingestion_status",
           side_effect=HTTPException(status_code=503, detail="Błąd bazy danych: db down"))
    def test_db_error_returns_503(self, mock_query):
        response = client.get("/api/v1/ingestion/status")

        assert response.status_code == 503
        assert "Błąd bazy danych" in response.json()["detail"]
