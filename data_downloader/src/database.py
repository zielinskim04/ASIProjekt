import psycopg2
import logging
import re
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
logger = logging.getLogger(__name__)

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "realestate"),
    "user": os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASSWORD", "admin"),
    "host": os.getenv("DB_HOST", "db"), 
    "port": int(os.getenv("DB_PORT", "5432"))
}

def clean_numeric(val):
    if not val or val == 'zapytaj': return None
    num = re.sub(r'[^\d.]', '', str(val).replace(' ', '').replace(',', '.'))
    return float(num) if num else None

def save_pois(pois):
    if not pois: return
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        inserted_pois = 0
        insert_poi_query = """
            INSERT INTO points_of_interest (osm_id, category, name, geom)
            VALUES (%s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
            ON CONFLICT (osm_id) DO NOTHING;
        """
        for poi in pois:
            cur.execute(insert_poi_query, (poi['osm_id'], poi['category'], poi['name'], poi['lon'], poi['lat']))
            inserted_pois += cur.rowcount
            
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"Baza Danych: Zapisano {inserted_pois} nowych obiektów infrastruktury (POI).")
    except Exception as e:
        logger.error(f"Błąd przy zapisie POI: {e}")

def save_to_postgres(df):
    if df.empty: return
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        inserted_props = 0

        insert_prop_query = """
            INSERT INTO properties (title, address_clean, price, area, rooms, link, geom)
            VALUES (%s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
            ON CONFLICT (link) DO NOTHING;
        """
        for index, row in df.iterrows():
            try:
                cur.execute(insert_prop_query, (
                    row['Tytuł'], row.get('Address_clean', row['Tytuł']), clean_numeric(row.get('Cena')),
                    clean_numeric(row.get('Metraż')), clean_numeric(row.get('Pokoje')), row['Link'], row['Lon'], row['Lat']
                ))
                inserted_props += cur.rowcount
            except Exception as e:
                conn.rollback() 
                continue
            
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"Baza Danych: Zapisano {inserted_props} nowych ofert nieruchomości.")
    except Exception as e:
        logger.error(f"Błąd połączenia z bazą: {e}")