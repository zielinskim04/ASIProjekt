import schedule
import time
import logging
from scraper import fetch_offers
from parser import process_offers
from database import save_to_postgres, save_pois
from geocoder import fetch_all_warsaw_pois

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def run_pipeline():
    logger.info("Rozpoczynam potok danych...")

    pois = fetch_all_warsaw_pois()
    save_pois(pois)

    raw_df = fetch_offers(max_pages=20)

    processed_df = process_offers(raw_df)

    if not processed_df.empty:
        logger.info("Przystępuję do zapisu ofert w bazie danych...")
        save_to_postgres(processed_df)
    else:
        logger.warning("Brak ofert do zapisu.")
        
    logger.info("Potok danych zakończony sukcesem!")

if __name__ == "__main__":
    logger.info("Uruchamiam potok Inżynierii Danych...")
    run_pipeline()
    
    schedule.every().day.at("02:00").do(run_pipeline)
    while True:
        schedule.run_pending()
        time.sleep(60)