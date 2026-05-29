import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from src.scraper import fetch_offers

MOCK_HTML_WITH_OFFER = """
<html>
    <body>
        <div data-offer-card="true">
            <h2>
                <a href="/mieszkania/warszawa/mokotow/12345">
                    <span class="line-clamp-1">Piękne mieszkanie na Mokotowie</span>
                    <span class="line-clamp-1">Jasne i przestronne</span>
                </a>
            </h2>
            <div class="flex w-full items-center text-sm">
                <p>850 000 zł</p>
                <p>55 m²</p>
                <p>3 pokoje</p>
            </div>
        </div>
    </body>
</html>
"""

MOCK_HTML_EMPTY = """
<html>
    <body>
        <div>Tu nie ma żadnych ofert</div>
    </body>
</html>
"""

class TestFetchOffers:

    @patch('src.scraper.requests.get')
    def test_fetch_offers_success_parses_html_correctly(self, mock_get):
        """
        Testuje czy scraper potrafi poprawnie wyciągnąć Tytuł, Cenę, Metraż i Pokoje
        ze spreparowanego (zamockowanego) kodu HTML.
        """

        mock_response = MagicMock()
        mock_response.text = MOCK_HTML_WITH_OFFER
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        df = fetch_offers(max_pages=1)

        assert not df.empty, "DataFrame nie powinien być pusty"
        assert len(df) == 1, "Powinna zostać znaleziona dokładnie 1 oferta"
        
        row = df.iloc[0]
        assert row['Tytuł'] == "Piękne mieszkanie na Mokotowie - Jasne i przestronne"
        assert row['Cena'] == "850 000 zł"
        assert row['Metraż'] == "55 m²"
        assert row['Pokoje'] == "3 pokoje"
        assert row['Link'] == "https://adresowo.pl/mieszkania/warszawa/mokotow/12345"

    @patch('src.scraper.requests.get')
    def test_fetch_offers_empty_page_breaks_loop(self, mock_get):
        """
        Testuje czy napotkanie pustej strony (bez ofert) przerywa działanie
        scrapera i zwraca pusty DataFrame.
        """
        mock_response = MagicMock()
        mock_response.text = MOCK_HTML_EMPTY
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        df = fetch_offers(max_pages=3)

        assert mock_get.call_count == 1
        assert df.empty, "DataFrame powinien być pusty, skoro nie było ofert"

    @patch('src.scraper.requests.get')
    def test_fetch_offers_handles_network_errors(self, mock_get):
        """
        Testuje zachowanie scrapera w przypadku błędu sieci (np. Timeout).
        Funkcja wciąż powinna zwrócić poprawny (nawet jeśli pusty) DataFrame.
        """
        from requests.exceptions import Timeout
        
        mock_get.side_effect = Timeout("Serwer nie odpowiada")

        df = fetch_offers(max_pages=2)

        assert df.empty
        assert isinstance(df, pd.DataFrame)