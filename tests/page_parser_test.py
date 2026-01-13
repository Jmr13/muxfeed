from data import EXISTING_URL, NONEXISTING_URL
from parsers.page_parser import PageParser

def test_page_parse_success():
    parser = PageParser()
    result = parser.get_content(EXISTING_URL)
    assert result != "Failed to fetch page."
    
def test_page_parse_failure():
    parser = PageParser()
    result = parser.get_content(NONEXISTING_URL)
    assert result == "Failed to fetch page."