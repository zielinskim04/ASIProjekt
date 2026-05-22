import time
import pandas as pd
import logging
from geocoder import clean_address_for_geo, geocode_address

logger = logging.getLogger(__name__)

def process_offers(df):
    if df.empty:
        return df

    logger.info(f"Zostało ofert: {len(df)}")
    
    processed_results = []

    for index, row in df.iterrows():
        title = row['Tytuł']
        logger.info(f"Geokodowanie [{index}]: {clean_address_for_geo(title)}")

        lat, lon = geocode_address(title)
        time.sleep(1.2)
        
        if lat and lon:
            processed_results.append({
                'Tytuł': title,
                'Address_clean': clean_address_for_geo(title),
                'Cena': row['Cena'],
                'Metraż': row['Metraż'],
                'Pokoje': row['Pokoje'],
                'Lat': lat,
                'Lon': lon,
                'Link': row['Link']
            })
        else:
            logger.warning(f"Lokalizacja nieznaleziona dla: {title}")

    return pd.DataFrame(processed_results)