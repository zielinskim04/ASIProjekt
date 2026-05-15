import requests
import logging
from tenacity import retry, stop_after_attempt, wait_random_exponential

logger = logging.getLogger(__name__)

def clean_address_for_geo(text):
    if ' - ' in text:
        parts = text.split(' - ')
        street = parts[-1].strip()
        city = parts[0].split(',')[0].strip()
        if street.startswith('ul. '):
            street = street[4:].strip()
        if not any(char.isdigit() for char in street):
            street = f"{street} 1"
        return f"{street}, {city}"
    return text

def geocode_address(address):
    clean_addr = clean_address_for_geo(address)
    url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(clean_addr)}&format=json&limit=1"
    headers = {'User-Agent': 'Property_Analysis_Bot_v2'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200 and response.json():
            data = response.json()[0]
            return float(data['lat']), float(data['lon'])
    except Exception as e:
        logger.error(f"Błąd Nominatim: {e}")
    return None, None

@retry(stop=stop_after_attempt(3), wait=wait_random_exponential(multiplier=2, max=30))
def fetch_all_warsaw_pois():
    logger.info("Pobieram WSZYSTKIE szkoły i przystanki dla Warszawy z Overpass API (to potrwa chwilę)...")
    headers = {'User-Agent': 'Property_Analysis_Bot_v2'}
    overpass_url = "https://overpass-api.de/api/interpreter"

    overpass_query = """
    [out:json][timeout:180];
    area["name"="Warszawa"]["admin_level"="8"]->.searchArea;
    (
      nwr["highway"="bus_stop"](area.searchArea);
      nwr["amenity"="school"](area.searchArea);
    );
    out center;
    """
    
    response = requests.post(overpass_url, data=overpass_query, headers=headers, timeout=200)
    response.raise_for_status()
    
    elements = response.json().get('elements', [])
    found_pois = []
    
    for element in elements:
        e_lat = element.get('lat') or element.get('center', {}).get('lat')
        e_lon = element.get('lon') or element.get('center', {}).get('lon')
        if not e_lat or not e_lon: continue
        
        osm_id = element.get('id')
        tags = element.get('tags', {})
        name = tags.get('name')
        
        category = 'bus_stop' if tags.get('highway') == 'bus_stop' else ('school' if tags.get('amenity') == 'school' else None)
            
        if category and osm_id:
            found_pois.append({'osm_id': osm_id, 'category': category, 'name': name, 'lat': e_lat, 'lon': e_lon})
            
    logger.info(f"SUKCES! Pobrane POI z Warszawy: {len(found_pois)} obiektów.")
    return found_pois