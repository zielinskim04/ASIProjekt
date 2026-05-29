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

EXPECTED_POI_CATEGORIES = {
    'bus_stop', 'school', 'hospital', 'cinema', 'theatre',
    'museum', 'pub', 'restaurant', 'cafe', 'bank', 'parking',
    'police', 'supermarket',
}

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

    
    run_poi_pipeline()

    run_properties_pipeline()

    schedule.every().day.at("02:00").do(run_properties_pipeline)
    schedule.every().monday.at("03:00").do(run_poi_pipeline)

    while True:
        schedule.run_pending()
        time.sleep(60)