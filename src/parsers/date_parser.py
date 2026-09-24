import locale
from contextlib import contextmanager
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, List

@contextmanager
def c_time_locale():
    previous = locale.setlocale(locale.LC_TIME)
    try:
        try:
            locale.setlocale(locale.LC_TIME, "C.UTF-8")
        except locale.Error:
            locale.setlocale(locale.LC_TIME, "C")
        yield
    finally:
        locale.setlocale(locale.LC_TIME, previous)

class DateParseStrategy(ABC):
    @abstractmethod
    def parse(self, date_str: str) -> Optional[datetime]:
        pass
            
class ISOFormatStrategy(DateParseStrategy):
    def parse(self, date_str: str) -> Optional[datetime]:
        try:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            return None

class ISOFormatTzStrategy(DateParseStrategy):
    def parse(self, date_str: str) -> Optional[datetime]:
        try:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z")
        except ValueError:
            return None

class ISOFormatMsStrategy(DateParseStrategy):
    def parse(self, date_str: str) -> Optional[datetime]:
        try:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f")
        except ValueError:
            return None

class ISOFormatMsTzStrategy(DateParseStrategy):
    def parse(self, date_str: str) -> Optional[datetime]:
        try:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z")
        except ValueError:
            return None

class ISOBasicStrategy(DateParseStrategy):
    def parse(self, date_str: str) -> Optional[datetime]:
        try:
            return datetime.strptime(date_str, "%Y%m%dT%H%M%S")
        except ValueError:
            return None

class ISOBasicTzStrategy(DateParseStrategy):
    def parse(self, date_str: str) -> Optional[datetime]:
        try:
            return datetime.strptime(date_str, "%Y%m%dT%H%M%S%z")
        except ValueError:
            return None
            
class RFCFormatStrategy(DateParseStrategy):
    def parse(self, date_str: str) -> Optional[datetime]:
        try:
            with c_time_locale():
                return datetime.strptime(
                    date_str,
                    "%a, %d %b %Y %H:%M:%S",
                )
        except (ValueError, locale.Error):
            return None

class RFCFormatTz1Strategy(DateParseStrategy):
    def parse(self, date_str: str) -> Optional[datetime]:
        try:
            with c_time_locale():
                dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
                return dt.replace(tzinfo=None)
        except (ValueError, TypeError, locale.Error):
            return None
            
class RFCFormatTz2Strategy(DateParseStrategy):
    def parse(self, date_str: str) -> Optional[datetime]:
        try:
            with c_time_locale():
                dt_parts = date_str.split()
                dt = datetime.strptime(
                    " ".join(dt_parts[:-1]),
                    "%a, %d %b %Y %H:%M:%S",
                )
                return dt
        except (ValueError, TypeError, IndexError, locale.Error):
            return None

class DateParser:
    """Strategy-based date parser that normalises heterogeneous feed date strings into
    a single ``"%B %d, %Y | %-I:%M %p"`` display format (e.g. ``"January 01, 2026 | 12:00 AM"``).

    All locale-sensitive operations (``strptime`` with ``%a``/``%b``/``%p`` and ``strftime``
    with ``%B``/``%p``) are wrapped in :func:`c_time_locale` to guarantee English output
    regardless of the system locale.

    .. note:: ``%-I`` strips the leading zero from the hour — it is supported on Linux and
       Termux but **not** on Windows.
    """

    def _getDateParseStrategy(self, date_str: str) -> DateParseStrategy:
        """Select the correct parsing strategy by inspecting the shape of *date_str*.

        ISO 8601 strings start with a digit; RFC 2822 strings start with an
        abbreviated weekday name (``%a``).  Within each family the strategy is
        further narrowed by the presence of a timezone suffix, fractional
        seconds, or the compact (no-dash) ISO basic format.
        """
        if not date_str:
            raise ValueError("Empty date string")

        if date_str[0].isdigit():
            # --- ISO 8601 family ---
            is_compact_format = "-" not in date_str[2:10]
            has_timezone_offset = date_str.endswith("+0000") or "+" in date_str[10:] or "-" in date_str[10:]
            has_fractional_seconds = "." in date_str

            if is_compact_format:
                if has_timezone_offset:
                    return ISOBasicTzStrategy()
                return ISOBasicStrategy()
            if has_fractional_seconds:
                if has_timezone_offset:
                    return ISOFormatMsTzStrategy()
                return ISOFormatMsStrategy()
            if has_timezone_offset:
                return ISOFormatTzStrategy()
            return ISOFormatStrategy()

        else:
            # --- RFC 2822 family ---
            if "+" in date_str:
                return RFCFormatTz1Strategy()
            elif len(date_str) > 5 and date_str[-5] == '-' and date_str[-4:].isdigit():
                # Numeric negative offset (e.g. "-0500")
                return RFCFormatTz1Strategy()
            elif date_str[-1].isalpha():
                # Timezone abbreviation (e.g. "PST", "UTC") — suffix is
                # stripped before parsing because strptime has no %z alias support.
                return RFCFormatTz2Strategy()
            else:
                return RFCFormatStrategy()

    def parse(self, date_str: Optional[str]) -> Optional[str]:
        """Normalise *date_str* to ``"%B %d, %Y | %-I:%M %p"`` or return ``None``.

        Before dispatching to a strategy the input is pre-processed:
        * ``Z`` is rewritten to ``+0000`` (Python's ``%z`` does not accept ``Z``).
        * Fractional seconds beyond microsecond precision (6 digits) are
          truncated so ``datetime.strptime`` does not raise ``ValueError``.
        """
        if not date_str:
            return None

        # Python's %z does not accept 'Z' — rewrite to numeric UTC offset.
        if date_str.endswith("Z"):
            date_str = date_str[:-1] + "+0000"

        # Truncate fractional seconds to 6 digits (microsecond precision).
        decimal_pos = date_str.find(".")
        if decimal_pos != -1:
            fractional_end = decimal_pos + 1
            while fractional_end < len(date_str) and date_str[fractional_end].isdigit():
                fractional_end += 1
            fractional_digits = fractional_end - decimal_pos - 1
            if fractional_digits > 6:
                date_str = date_str[:decimal_pos + 7] + date_str[fractional_end:]

        strategy = self._getDateParseStrategy(date_str)
        parsed_datetime: Optional[datetime] = strategy.parse(date_str)

        if parsed_datetime is None:
            return None

        with c_time_locale():
            return parsed_datetime.strftime("%B %d, %Y | %-I:%M %p")