import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from src.database import (
    query_properties,
    query_property_with_pois,
    query_ingestion_status,
)

MODULE = "src.database"

# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_cursor():
    cur = MagicMock()
    cur.__enter__.return_value = cur
    cur.__exit__.return_value = False
    return cur


def _make_conn(cur):
    conn = MagicMock()
    conn.__enter__.return_value = conn
    conn.__exit__.return_value = False
    conn.cursor.return_value = cur
    return conn


# ── query_properties ──────────────────────────────────────────────────────────

class TestQueryProperties:

    @patch(f"{MODULE}.psycopg2.connect")
    def test_no_filters_contains_only_base_condition(self, mock_connect):
        cur = _make_cursor()
        cur.fetchall.return_value = []
        mock_connect.return_value = _make_conn(cur)

        query_properties()

        sql, _ = cur.execute.call_args[0]
        assert "p.geom IS NOT NULL" in sql
        assert "p.price >=" not in sql
        assert "p.price <=" not in sql
        assert "p.area >=" not in sql
        assert "p.rooms >=" not in sql

    @patch(f"{MODULE}.psycopg2.connect")
    def test_price_min_and_max_added_to_sql(self, mock_connect):
        cur = _make_cursor()
        cur.fetchall.return_value = []
        mock_connect.return_value = _make_conn(cur)

        query_properties(price_min=300_000, price_max=700_000)

        sql, params = cur.execute.call_args[0]
        assert "p.price >= %s" in sql
        assert "p.price <= %s" in sql
        assert 300_000 in params
        assert 700_000 in params

    @patch(f"{MODULE}.psycopg2.connect")
    def test_only_price_min_no_max_condition(self, mock_connect):
        cur = _make_cursor()
        cur.fetchall.return_value = []
        mock_connect.return_value = _make_conn(cur)

        query_properties(price_min=200_000)

        sql, params = cur.execute.call_args[0]
        assert "p.price >= %s" in sql
        assert "p.price <= %s" not in sql
        assert 200_000 in params

    @patch(f"{MODULE}.psycopg2.connect")
    def test_area_filter_added_to_sql(self, mock_connect):
        cur = _make_cursor()
        cur.fetchall.return_value = []
        mock_connect.return_value = _make_conn(cur)

        query_properties(area_min=40, area_max=80)

        sql, params = cur.execute.call_args[0]
        assert "p.area >= %s" in sql
        assert "p.area <= %s" in sql
        assert 40 in params
        assert 80 in params

    @patch(f"{MODULE}.psycopg2.connect")
    def test_rooms_filter_added_to_sql(self, mock_connect):
        cur = _make_cursor()
        cur.fetchall.return_value = []
        mock_connect.return_value = _make_conn(cur)

        query_properties(rooms_min=2, rooms_max=3)

        sql, params = cur.execute.call_args[0]
        assert "p.rooms >= %s" in sql
        assert "p.rooms <= %s" in sql
        assert 2 in params
        assert 3 in params

    @patch(f"{MODULE}.psycopg2.connect")
    def test_price_per_sqm_filter_added_to_sql(self, mock_connect):
        cur = _make_cursor()
        cur.fetchall.return_value = []
        mock_connect.return_value = _make_conn(cur)

        query_properties(price_per_sqm_max=12_000)

        sql, params = cur.execute.call_args[0]
        assert "(p.price / p.area) <= %s" in sql
        assert 12_000 in params

    @patch(f"{MODULE}.psycopg2.connect")
    def test_poi_filter_adds_exists_subquery(self, mock_connect):
        cur = _make_cursor()
        cur.fetchall.return_value = []
        mock_connect.return_value = _make_conn(cur)

        query_properties(poi_category="bus_stop", poi_radius_m=500)

        sql, params = cur.execute.call_args[0]
        assert "EXISTS" in sql
        assert "points_of_interest" in sql
        assert "ST_DWithin" in sql
        assert "bus_stop" in params
        assert 500 in params

    @patch(f"{MODULE}.psycopg2.connect")
    def test_limit_is_always_last_param(self, mock_connect):
        cur = _make_cursor()
        cur.fetchall.return_value = []
        mock_connect.return_value = _make_conn(cur)

        query_properties(price_min=100_000, rooms_min=2, limit=42)

        _, params = cur.execute.call_args[0]
        assert params[-1] == 42

    @patch(f"{MODULE}.psycopg2.connect")
    def test_all_filters_combined(self, mock_connect):
        cur = _make_cursor()
        cur.fetchall.return_value = []
        mock_connect.return_value = _make_conn(cur)

        query_properties(
            price_min=200_000, price_max=800_000,
            area_min=35, area_max=100,
            rooms_min=1, rooms_max=4,
            price_per_sqm_max=15_000,
            poi_category="school", poi_radius_m=1000,
        )

        sql, params = cur.execute.call_args[0]
        assert "p.price >= %s" in sql
        assert "p.price <= %s" in sql
        assert "p.area >= %s" in sql
        assert "p.area <= %s" in sql
        assert "p.rooms >= %s" in sql
        assert "p.rooms <= %s" in sql
        assert "(p.price / p.area) <= %s" in sql
        assert "ST_DWithin" in sql
        assert "school" in params
        assert 1000 in params

    @patch(f"{MODULE}.psycopg2.connect")
    def test_returns_list_of_dicts(self, mock_connect):
        row = {
            "id": 1, "title": "Mokotów 50m²", "price": 650_000.0,
            "area": 50.0, "rooms": 2, "address_clean": "ul. Puławska 10",
            "link": "https://adresowo.pl/1", "scraped_at": None,
            "lat": 52.19, "lon": 21.02, "price_per_sqm": 13_000,
        }
        cur = _make_cursor()
        cur.fetchall.return_value = [row]
        mock_connect.return_value = _make_conn(cur)

        result = query_properties()

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["price"] == 650_000.0

    @patch(f"{MODULE}.psycopg2.connect")
    def test_empty_result_returns_empty_list(self, mock_connect):
        cur = _make_cursor()
        cur.fetchall.return_value = []
        mock_connect.return_value = _make_conn(cur)

        result = query_properties()

        assert result == []

    @patch(f"{MODULE}.psycopg2.connect")
    def test_db_connection_error_raises_503(self, mock_connect):
        mock_connect.side_effect = Exception("connection refused")

        with pytest.raises(HTTPException) as exc_info:
            query_properties()

        assert exc_info.value.status_code == 503
        assert "Błąd bazy danych" in exc_info.value.detail


# ── query_property_with_pois ──────────────────────────────────────────────────

class TestQueryPropertyWithPois:

    def _prop_row(self, prop_id=5):
        return {
            "id": prop_id, "title": "Śródmieście", "price": 900_000.0,
            "area": 60.0, "rooms": 3, "address_clean": "ul. Marszałkowska 1",
            "link": "https://adresowo.pl/5", "scraped_at": None,
            "lat": 52.23, "lon": 21.01, "price_per_sqm": 15_000,
        }

    @patch(f"{MODULE}.psycopg2.connect")
    def test_returns_property_with_nearest_pois(self, mock_connect):
        poi_rows = [
            {"id": 10, "category": "bus_stop", "name": "Marszałkowska",
             "lat": 52.231, "lon": 21.011, "distance_m": 60},
            {"id": 11, "category": "cafe", "name": "Cafe Mokka",
             "lat": 52.232, "lon": 21.012, "distance_m": 120},
        ]
        cur = _make_cursor()
        cur.fetchone.return_value = self._prop_row()
        cur.fetchall.return_value = poi_rows
        mock_connect.return_value = _make_conn(cur)

        result = query_property_with_pois(5)

        assert result["id"] == 5
        assert "nearest_pois" in result
        assert len(result["nearest_pois"]) == 2
        assert result["nearest_pois"][0]["distance_m"] == 60

    @patch(f"{MODULE}.psycopg2.connect")
    def test_property_not_found_raises_404(self, mock_connect):
        cur = _make_cursor()
        cur.fetchone.return_value = None
        mock_connect.return_value = _make_conn(cur)

        with pytest.raises(HTTPException) as exc_info:
            query_property_with_pois(999)

        assert exc_info.value.status_code == 404

    @patch(f"{MODULE}.psycopg2.connect")
    def test_property_with_no_pois_nearby(self, mock_connect):
        cur = _make_cursor()
        cur.fetchone.return_value = self._prop_row()
        cur.fetchall.return_value = []
        mock_connect.return_value = _make_conn(cur)

        result = query_property_with_pois(5)

        assert result["nearest_pois"] == []

    @patch(f"{MODULE}.psycopg2.connect")
    def test_poi_query_uses_correct_property_id(self, mock_connect):
        cur = _make_cursor()
        cur.fetchone.return_value = self._prop_row(prop_id=7)
        cur.fetchall.return_value = []
        mock_connect.return_value = _make_conn(cur)

        query_property_with_pois(7)

        # Second execute = POI query — must reference property_id 7
        poi_call_params = cur.execute.call_args_list[1][0][1]
        assert 7 in poi_call_params

    @patch(f"{MODULE}.psycopg2.connect")
    def test_db_error_raises_503(self, mock_connect):
        mock_connect.side_effect = Exception("timeout")

        with pytest.raises(HTTPException) as exc_info:
            query_property_with_pois(1)

        assert exc_info.value.status_code == 503


# ── query_ingestion_status ────────────────────────────────────────────────────

class TestQueryIngestionStatus:

    @patch(f"{MODULE}.psycopg2.connect")
    def test_returns_all_required_keys(self, mock_connect):
        cur = _make_cursor()
        cur.fetchone.side_effect = [
            {"last_scraped_at": "2026-05-29 06:00:00", "total_properties": 150},
            {"total_pois": 9200},
        ]
        cur.fetchall.return_value = [
            {"category": "bus_stop", "count": 3500},
        ]
        mock_connect.return_value = _make_conn(cur)

        result = query_ingestion_status()

        assert "last_scraped_at" in result
        assert "total_properties" in result
        assert "total_pois" in result
        assert "poi_categories" in result

    @patch(f"{MODULE}.psycopg2.connect")
    def test_poi_categories_is_dict_keyed_by_category(self, mock_connect):
        cur = _make_cursor()
        cur.fetchone.side_effect = [
            {"last_scraped_at": None, "total_properties": 0},
            {"total_pois": 0},
        ]
        cur.fetchall.return_value = [
            {"category": "bus_stop",   "count": 3000},
            {"category": "school",     "count": 400},
            {"category": "restaurant", "count": 1200},
        ]
        mock_connect.return_value = _make_conn(cur)

        result = query_ingestion_status()

        assert result["poi_categories"]["bus_stop"] == 3000
        assert result["poi_categories"]["school"] == 400
        assert result["poi_categories"]["restaurant"] == 1200

    @patch(f"{MODULE}.psycopg2.connect")
    def test_counts_match_mock_values(self, mock_connect):
        cur = _make_cursor()
        cur.fetchone.side_effect = [
            {"last_scraped_at": "2026-01-01", "total_properties": 275},
            {"total_pois": 8750},
        ]
        cur.fetchall.return_value = []
        mock_connect.return_value = _make_conn(cur)

        result = query_ingestion_status()

        assert result["total_properties"] == 275
        assert result["total_pois"] == 8750

    @patch(f"{MODULE}.psycopg2.connect")
    def test_db_error_raises_503(self, mock_connect):
        mock_connect.side_effect = Exception("db down")

        with pytest.raises(HTTPException) as exc_info:
            query_ingestion_status()

        assert exc_info.value.status_code == 503
        assert "Błąd bazy danych" in exc_info.value.detail
