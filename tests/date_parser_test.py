import pytest

from src.parsers.date_parser import DateParser


EXPECTED_DATE_TIME = "January 01, 2026 | 12:00 AM"


# ISO 8601 inputs
ISO_CASES = [
    # UTC
    ("2026-01-01T00:00:00Z", "January 01, 2026 | 12:00 AM"),

    # Naive datetime
    ("2026-01-01T00:00:00", "January 01, 2026 | 12:00 AM"),

    # Explicit UTC offset
    ("2025-12-31T16:00:00+08:00", "December 31, 2025 | 4:00 PM"),

    # +05:30 offset
    ("2025-12-31T18:30:00+05:30", "December 31, 2025 | 6:30 PM"),

    # -16:00 offset
    ("2026-01-01T16:00:00-16:00", "January 01, 2026 | 4:00 PM"),

    # -05:00 offset
    ("2026-01-01T05:00:00-0500", "January 01, 2026 | 5:00 AM"),

    # +08:00 compact offset
    ("2025-12-31T16:00:00+0800", "December 31, 2025 | 4:00 PM"),

    # Fractional seconds
    ("2026-01-01T00:00:00.000Z", "January 01, 2026 | 12:00 AM"),

    # Invalid hour 24
    ("2026-01-01T24:00:00", None),
]


# RFC 2822 inputs with numeric timezone offsets
RFC_CASES = [
    # No timezone
    ("Thu, 01 Jan 2026 00:00:00", "January 01, 2026 | 12:00 AM"),

    # +08:00 midnight UTC
    ("Wed, 31 Dec 2025 16:00:00 +0800", "December 31, 2025 | 4:00 PM"),

    # -05:00 midnight UTC
    ("Thu, 01 Jan 2026 05:00:00 -0500", "January 01, 2026 | 5:00 AM"),

    # UTC
    ("Thu, 01 Jan 2026 00:00:00 +0000", "January 01, 2026 | 12:00 AM"),
]


# RFC 2822 inputs with timezone abbreviations
RFC_TZ_ABBREV_CASES = [
    # PST = UTC-8
    ("Thu, 01 Jan 2026 08:00:00 PST", "January 01, 2026 | 8:00 AM"),

    # UTC
    ("Thu, 01 Jan 2026 00:00:00 UTC", "January 01, 2026 | 12:00 AM"),

    # GMT = UTC
    ("Thu, 01 Jan 2026 00:00:00 GMT", "January 01, 2026 | 12:00 AM"),

    # JST = UTC+9
    ("Thu, 01 Jan 2026 09:00:00 JST", "January 01, 2026 | 9:00 AM"),

    # IST = UTC+5:30
    ("Thu, 01 Jan 2026 05:30:00 IST", "January 01, 2026 | 5:30 AM"),
]


# Invalid or unsupported inputs
NONE_CASES = [
    (None, None),
    ("", None),
    ("invalid date string", None),
    ("2026-01-01", None),
    ("Thu, 01 Jan 2026 00:00:00 XYZ", None),
]


# RFC 3339 date/time inputs.
# Each valid input is expected to preserve its supplied local datetime
# and timezone offset when formatted.
RFC3339_VALID_CASES = [
    # UTC
    ("2026-01-01T00:00:00Z", "January 01, 2026 | 12:00 AM"),

    # +08:00
    ("2025-12-31T16:00:00+08:00", "December 31, 2025 | 4:00 PM"),

    # -05:00
    ("2026-01-01T05:00:00-05:00", "January 01, 2026 | 5:00 AM"),

    # Fractional seconds
    ("2026-01-01T00:00:00.1Z", "January 01, 2026 | 12:00 AM"),
    ("2026-01-01T00:00:00.12Z", "January 01, 2026 | 12:00 AM"),
    ("2026-01-01T00:00:00.123Z", "January 01, 2026 | 12:00 AM"),
    ("2026-01-01T00:00:00.1234Z", "January 01, 2026 | 12:00 AM"),
    ("2026-01-01T00:00:00.12345Z", "January 01, 2026 | 12:00 AM"),
    ("2026-01-01T00:00:00.123456Z", "January 01, 2026 | 12:00 AM"),

    # Midnight UTC
    ("2026-01-01T00:00:00Z", "January 01, 2026 | 12:00 AM"),

    # Explicit UTC offset
    ("2026-01-01T00:00:00+00:00", "January 01, 2026 | 12:00 AM"),

    # Unknown local offset (-00:00)
    ("2026-01-01T00:00:00-00:00", "January 01, 2026 | 12:00 AM"),

    # Milliseconds with positive offset
    ("2025-12-31T16:00:00.000+08:00", "December 31, 2025 | 4:00 PM"),

    # Milliseconds with negative offset
    ("2026-01-01T05:00:00.000-05:00", "January 01, 2026 | 5:00 AM"),

    # Uppercase canonical form
    ("2026-01-01T00:00:00Z", "January 01, 2026 | 12:00 AM"),

    # Offset without colon
    ("2025-12-31T16:00:00+0800", "December 31, 2025 | 4:00 PM"),

    # Compact ISO-style form
    ("20260101T000000Z", "January 01, 2026 | 12:00 AM"),
]


# Invalid RFC 3339 formats
RFC3339_INVALID_CASES = [
    # Date-only
    ("2026-01-01", None),

    # Time-only
    ("00:00:00Z", None),

    # Time-only positive offset
    ("00:00:00+08:00", None),

    # Time-only negative offset
    ("00:00:00-05:00", None),

    # Space instead of T
    ("2026-01-01 00:00:00", None),

    # Lowercase timezone
    ("2026-01-01t00:00:00z", None),

    # More than Python's supported microsecond precision (truncated to 6 digits)
    ("2026-01-01T00:00:00.123456789Z", "January 01, 2026 | 12:00 AM"),

    # Slash-based date
    ("01/01/2026 00:00:00", None),

    # Text date
    ("January 01, 2026 00:00:00", None),

    # 12-hour format without seconds
    ("2026-01-01 12:00 AM", None),

    # Missing seconds
    ("2026-01-01T00:00Z", None),

    # UTC text instead of numeric offset
    ("2026-01-01T00:00:00 UTC", None),
]


# Aggregate representative cases across the supported ISO 8601 and RFC 2822
# formats, including timezone offsets, timezone abbreviations, and invalid inputs.
ALL_CASES = ISO_CASES + RFC_CASES + RFC_TZ_ABBREV_CASES + NONE_CASES

# Combine valid and invalid RFC 3339 cases to verify both successful parsing
# and graceful rejection of malformed or unsupported date/time formats.
ALL_RFC3339_CASES = RFC3339_VALID_CASES + RFC3339_INVALID_CASES


@pytest.mark.parametrize("date_str, expected", ALL_CASES)
def test_dateparser_parse(date_str, expected):
    date_parser = DateParser()
    assert date_parser.parse(date_str) == expected


@pytest.mark.parametrize("date_str, expected", ALL_RFC3339_CASES)
def test_dateparser_parse_rfc3339(date_str, expected):
    date_parser = DateParser()
    assert date_parser.parse(date_str) == expected