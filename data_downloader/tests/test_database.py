import pytest
from src.database import clean_numeric

@pytest.mark.parametrize("input_val, expected", [
    ("1 200 000", 1200000.0),
    ("45,50", 45.50),
    ("zapytaj", None),
    (None, None),
    (" 99.9 ", 99.9),
    ("500 000 zł", 500000.0)
])
def test_clean_numeric(input_val, expected):
    assert clean_numeric(input_val) == expected