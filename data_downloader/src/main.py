import schedule
import time
import logging
import psycopg2
import os
from scraper import fetch_offers
from parser import process_offers
from database import save_to_postgres, save_pois, DB_CONFIG
from geocoder import fetch_all_warsaw_pois

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def db_is_empty():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM properties")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count == 0
    except Exception as e:
        logger.warning(f"Nie można sprawdzić stanu bazy: {e}")
        return True

EXPECTED_POI_CATEGORIES = {
    'bus_stop', 'school', 'hospital', 'cinema', 'theatre',
    'museum', 'pub', 'restaurant', 'cafe', 'bank', 'parking',
    'police', 'supermarket',
}

def pois_need_update():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT category FROM points_of_interest")
        existing = {row[0] for row in cur.fetchall()}
        cur.close()
        conn.close()
        missing = EXPECTED_POI_CATEGORIES - existing
        if missing:
            logger.info(f"Brakujące kategorie POI: {missing} — pobieram od nowa.")
            return True
        return False
    except Exception as e:
        logger.warning(f"Nie można sprawdzić kategorii POI: {e}")
        return True

def run_poi_pipeline():
    logger.info("Pobieram punkty infrastruktury (POI)...")
    pois = fetch_all_warsaw_pois()
    save_pois(pois)
    logger.info("POI zaktualizowane.")

def run_properties_pipeline():
    logger.info("Pobieram oferty mieszkań...")
    raw_df = fetch_offers(max_pages=3)
    processed_df = process_offers(raw_df)
    if not processed_df.empty:
        save_to_postgres(processed_df)
    else:
        logger.warning("Brak ofert do zapisu.")
    logger.info("Oferty zaktualizowane.")

if __name__ == "__main__":
    logger.info("Uruchamiam potok Inżynierii Danych...")

    if pois_need_update():
        run_poi_pipeline()

    if db_is_empty():
        logger.info("Brak ofert w bazie — pobieram pierwszy raz.")
        run_properties_pipeline()
    else:
        logger.info("Baza zawiera już dane — pomijam pobieranie przy starcie.")

    # Oferty — codziennie (zmieniają się często)
    schedule.every().day.at("02:00").do(run_properties_pipeline)
    # POI — raz w tygodniu (infrastruktura miasta zmienia się rzadko)
    schedule.every().monday.at("03:00").do(run_poi_pipeline)

    while True:
        schedule.run_pending()
        time.sleep(60)