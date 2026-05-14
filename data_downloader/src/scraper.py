import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
import time 

logger = logging.getLogger(__name__)

def fetch_offers(base_url='https://adresowo.pl/mieszkania/warszawa/', max_pages=20):
    """
    Pobiera oferty z wielu stron. 
    max_pages - ile stron ofert chcemy przejrzeć.
    """
    logger.info(f"Rozpoczynam pobieranie ofert (max stron: {max_pages})...")
    headers = {
        'User-Agent': 'Projekt z architektury systemow informatycznych - Piotr Wysocki, Milosz Zielinski',
        'Accept-Language': 'pl-PL,pl;q=0.9'
    }
    
    all_scraped_data = []
    
    for page in range(1, max_pages + 1):
        if page == 1:
            url = base_url
        else:
            base_clean = base_url.rstrip('/')
            url = f"{base_clean}/_l{page}"
            
        logger.info(f"Pobieram stronę {page}: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            offers = soup.find_all('div', attrs={'data-offer-card': True})

            if not offers:
                logger.warning(f"Brak ofert na stronie {page}. Przerywam pobieranie kolejnych.")
                break
            
            page_data = []
            
            for offer in offers:
                try:
                    a_tag = offer.find('h2').find('a')
                    link = 'https://adresowo.pl' + a_tag['href']
                    
                    title_spans = a_tag.find_all('span', class_='line-clamp-1')
                    title = ' - '.join([span.text.strip() for span in title_spans if span.text.strip()])
                    
                    params_container = offer.find('div', class_='flex w-full items-center text-sm')
                    params = params_container.find_all('p') if params_container else []
                    
                    price = params[0].text.strip().replace('\xa0', ' ') if len(params) > 0 else None
                    area = params[1].text.strip() if len(params) > 1 else None
                    rooms = params[2].text.strip() if len(params) > 2 else None
                    
                    page_data.append({
                        'Tytuł': title,
                        'Cena': price,
                        'Metraż': area,
                        'Pokoje': rooms,
                        'Link': link
                    })
                except Exception as e:
                    logger.debug(f'Pominięto ogłoszenie ze względu na błąd parsowania: {e}')
                    continue
         
            all_scraped_data.extend(page_data)
            logger.info(f"Pobrano {len(page_data)} ofert z podstrony nr {page}.")
            
            if page < max_pages:
                time.sleep(2.5)
                
        except Exception as e:
            logger.error(f"Błąd krytyczny przy pobieraniu strony {page}: {e}")
            break 
            
    df = pd.DataFrame(all_scraped_data)
    logger.info(f"Zakończono scrapowanie. Łącznie zebrano {len(df)} ofert.")
    return df