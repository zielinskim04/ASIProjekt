import psycopg2
import psycopg2.extras
import os
from contextlib import contextmanager
from fastapi import HTTPException

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "realestate"),
    "user": os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASSWORD", "admin"),
    "host": os.getenv("DB_HOST", "db"),
    "port": int(os.getenv("DB_PORT", "5432")),
}

_PROPERTY_COLUMNS = """
    p.id, p.title, p.address_clean, p.price, p.area, p.rooms, p.link,
    p.scraped_at,
    ST_Y(p.geom) AS lat,
    ST_X(p.geom) AS lon,
    CASE WHEN p.area > 0 AND p.price IS NOT NULL
         THEN ROUND((p.price / p.area)::numeric, 0)
         ELSE NULL END AS price_per_sqm
"""


@contextmanager
def get_db():
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        yield conn
    finally:
        conn.close()


def query_properties(
    price_min=None,
    price_max=None,
    area_min=None,
    area_max=None,
    rooms_min=None,
    rooms_max=None,
    price_per_sqm_max=None,
    poi_category=None,
    poi_radius_m=500,
    limit=300,
):
    conditions = ["p.geom IS NOT NULL"]
    params = []

    if price_min is not None:
        conditions.append("p.price >= %s")
        params.append(price_min)
    if price_max is not None:
        conditions.append("p.price <= %s")
        params.append(price_max)
    if area_min is not None:
        conditions.append("p.area >= %s")
        params.append(area_min)
    if area_max is not None:
        conditions.append("p.area <= %s")
        params.append(area_max)
    if rooms_min is not None:
        conditions.append("p.rooms >= %s")
        params.append(rooms_min)
    if rooms_max is not None:
        conditions.append("p.rooms <= %s")
        params.append(rooms_max)
    if price_per_sqm_max is not None:
        conditions.append("p.price IS NOT NULL AND p.area > 0 AND (p.price / p.area) <= %s")
        params.append(price_per_sqm_max)
    if poi_category:
        conditions.append(
            "EXISTS ("
            "  SELECT 1 FROM points_of_interest poi"
            "  WHERE poi.category = %s"
            "  AND ST_DWithin(p.geom::geography, poi.geom::geography, %s)"
            ")"
        )
        params.append(poi_category)
        params.append(poi_radius_m)

    where = " AND ".join(conditions)
    sql = f"""
        SELECT {_PROPERTY_COLUMNS}
        FROM properties p
        WHERE {where}
        ORDER BY p.scraped_at DESC
        LIMIT %s
    """
    params.append(limit)

    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, params)
                return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Błąd bazy danych: {e}")


def query_property_with_pois(property_id: int):
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    f"SELECT {_PROPERTY_COLUMNS} FROM properties p"
                    " WHERE p.id = %s AND p.geom IS NOT NULL",
                    (property_id,),
                )
                prop = cur.fetchone()
                if not prop:
                    raise HTTPException(status_code=404, detail="Nieruchomość nie znaleziona")
                prop = dict(prop)

                cur.execute(
                    """
                    SELECT
                        poi.id, poi.category, poi.name,
                        ST_Y(poi.geom) AS lat,
                        ST_X(poi.geom) AS lon,
                        ROUND(ST_Distance(p.geom::geography, poi.geom::geography)::numeric, 0) AS distance_m
                    FROM points_of_interest poi, properties p
                    WHERE p.id = %s
                    ORDER BY ST_Distance(p.geom::geography, poi.geom::geography)
                    LIMIT 20
                    """,
                    (property_id,),
                )
                prop["nearest_pois"] = [dict(r) for r in cur.fetchall()]
                return prop
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Błąd bazy danych: {e}")


def query_ingestion_status():
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT MAX(scraped_at) AS last_scraped_at,"
                    "       COUNT(*) AS total_properties"
                    " FROM properties"
                )
                stats = dict(cur.fetchone())

                cur.execute("SELECT COUNT(*) AS total_pois FROM points_of_interest")
                stats["total_pois"] = cur.fetchone()["total_pois"]

                cur.execute(
                    "SELECT category, COUNT(*) AS count"
                    " FROM points_of_interest"
                    " GROUP BY category ORDER BY count DESC"
                )
                stats["poi_categories"] = {r["category"]: r["count"] for r in cur.fetchall()}
                return stats
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Błąd bazy danych: {e}")
