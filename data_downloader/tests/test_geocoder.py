import pytest
from src.geocoder import clean_address_for_geo

@pytest.mark.parametrize("input_address, expected_output", [
    ("Warszawa, Mokotów - ul. Puławska 123", "Puławska 123, Warszawa"),
    ("Warszawa, Śródmieście - Marszałkowska", "Marszałkowska 1, Warszawa"),
    ("Kraków, Stare Miasto - ul. Floriańska 12", "Floriańska 12, Kraków"),
    ("Wrocław - ul. Legnicka", "Legnicka 1, Wrocław"),
    ("Zwykły adres bez formatu", "Zwykły adres bez formatu"),
])
def test_clean_address_for_geo(input_address, expected_output):
    """
    Testuje poprawność czyszczenia adresów z portalu adresowo.pl.
    """
    result = clean_address_for_geo(input_address)
    assert result == expected_output