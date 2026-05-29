from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from .database import query_properties, query_property_with_pois, query_ingestion_status

app = FastAPI(title="ASI Nieruchomości API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/api/v1/properties")
def get_properties(
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    area_min: Optional[float] = None,
    area_max: Optional[float] = None,
    rooms_min: Optional[int] = None,
    rooms_max: Optional[int] = None,
    price_per_sqm_max: Optional[float] = None,
    poi_category: Optional[str] = None,
    poi_radius_m: int = Query(default=500, ge=50, le=5000),
    limit: int = Query(default=300, ge=1, le=1000),
):
    return query_properties(
        price_min=price_min,
        price_max=price_max,
        area_min=area_min,
        area_max=area_max,
        rooms_min=rooms_min,
        rooms_max=rooms_max,
        price_per_sqm_max=price_per_sqm_max,
        poi_category=poi_category,
        poi_radius_m=poi_radius_m,
        limit=limit,
    )


@app.get("/api/v1/properties/{property_id}")
def get_property(property_id: int):
    return query_property_with_pois(property_id)


@app.get("/api/v1/ingestion/status")
def get_ingestion_status():
    return query_ingestion_status()
