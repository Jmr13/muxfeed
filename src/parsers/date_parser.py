from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, List


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
            return datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S")
        except ValueError:
            return None

class RFCFormatTz1Strategy(DateParseStrategy):
    def parse(self, date_str: str) -> Optional[datetime]:
        try:
            dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
            return dt.replace(tzinfo=None)
        except (ValueError, TypeError):
            return None
            
class RFCFormatTz2Strategy(DateParseStrategy):
    TZ_OFFSETS = {
        "PST": -8,
        "PDT": -7,
        "MST": -7,
        "MDT": -6,
        "CST": -6,
        "CDT": -5,
        "EST": -5,
        "EDT": -4,
        "GMT": 0,
        "UTC": 0,
        "CET": 1,
        "CEST": 2,
        "IST": 5.5,
        "JST": 9,
        "AEST": 10,
        "AEDT": 11,
    }

    def parse(self, date_str: str) -> Optional[datetime]:
        try:
            # Get the timezone
            *dt_parts, tz = date_str.split()
            offset = self.TZ_OFFSETS.get(tz)
    
            # Convert the timezone abbreviation to UTC
            dt = datetime.strptime(" ".join(dt_parts), "%a, %d %b %Y %H:%M:%S")
            return dt - timedelta(hours=offset)
        except (ValueError, TypeError, IndexError):
            return None

class DateParser:
    def _getDateParseStrategy(self, date_str: str) -> DateParseStrategy:
        if not date_str:
            raise ValueError("Empty date string")

        if date_str[0].isdigit():
            is_basic = "-" not in date_str[2:10]
            has_tz = date_str.endswith("+0000") or "+" in date_str[10:] or "-" in date_str[10:]
            has_fractional = "." in date_str

            if is_basic:
                if has_tz:
                    return ISOBasicTzStrategy()
                return ISOBasicStrategy()
            if has_fractional:
                if has_tz:
                    return ISOFormatMsTzStrategy()
                return ISOFormatMsStrategy()
            if has_tz:
                return ISOFormatTzStrategy()
            return ISOFormatStrategy()

        else:
            if "+" in date_str:
                return RFCFormatTz1Strategy()
            elif len(date_str) > 5 and date_str[-5] == '-' and date_str[-4:].isdigit():
                return RFCFormatTz1Strategy()
            elif date_str[-1].isalpha():
                return RFCFormatTz2Strategy()
            else:
                return RFCFormatStrategy()

    def parse(self, date_str: Optional[str]) -> Optional[str]:
        if not date_str:
            return None

        if date_str.endswith("Z"):
            date_str = date_str[:-1] + "+0000"

        strategy = self._getDateParseStrategy(date_str)
        dt: Optional[datetime] = strategy.parse(date_str)

        if dt is None:
            return None

        return dt.strftime("%B %d, %Y | %-I:%M %p")