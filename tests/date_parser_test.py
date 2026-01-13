import pytest
from src.parsers.date_parser import DateParser
from data import CASES

@pytest.mark.parametrize("date_str, expected", CASES)
def test_dateparser_parse(date_str, expected):
    date_parser = DateParser()
    assert date_parser.parse(date_str) == expected