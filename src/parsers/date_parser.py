import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from src.config import TZ_OFFSETS

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
            
class RFCFormatStrategy(DateParseStrategy):
    def parse(self, date_str: str) -> Optional[datetime]:
        try:
            return datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S")
        except ValueError:
            return None

class RFCFormatTz1Strategy(DateParseStrategy):
    def parse(self, date_str: str) -> Optional[datetime]:
        try:
            return datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
        except Exception:
            return None
            
class RFCFormatTz2Strategy(DateParseStrategy):
    def parse(self, date_str: str) -> Optional[datetime]:
        try:
            # Get the timezone
            *dt_parts, tz = date_str.split()
            offset = TZ_OFFSETS.get(tz)
    
            # Convert the timezone abbreviation to UTC
            dt = datetime.strptime(" ".join(dt_parts), "%a, %d %b %Y %H:%M:%S")
            utc_time = dt - timedelta(hours=offset)
            local_offset = -time.timezone / 3600
            
            return utc_time + timedelta(hours=local_offset)
        except Exception:
            return None

class DateParseStrategyResolver:
    def __init__(self):
        self.iso = ISOFormatStrategy()
        self.iso_tz = ISOFormatTzStrategy()
        self.rfc = RFCFormatStrategy()
        self.rfc_tz1 = RFCFormatTz1Strategy()
        self.rfc_tz2 = RFCFormatTz2Strategy()

    def resolve(self, date_str: str) -> DateParseStrategy:
        if not date_str:
            raise ValueError("Empty date string")

        # ISO format (e.g. 2023-10-05T14:48:00)
        if "T" in date_str:
            if "+" in date_str or "-" in date_str[-6:]:
                return self.iso_tz
            return self.iso

        # RFC formats (e.g. Tue, 10 Oct 2023 14:48:00 GMT)
        if "," in date_str:
            parts = date_str.split()

            # Numeric timezone offset
            if parts and (parts[-1].startswith("+") or parts[-1].startswith("-")):
                return self.rfc_tz1

            # Named timezone (GMT, EST, etc.)
            if parts and parts[-1].isalpha():
                return self.rfc_tz2

            return self.rfc

        # Fallback
        return self.iso
    
class DateParser:
    def __init__(self, resolver: Optional[DateParseStrategyResolver] = None):
        self.resolver = resolver or DateParseStrategyResolver()

    def _convert_into_local_timezone(self, date_str: str) -> Optional[str]:
        if date_str.tzinfo and date_str.utcoffset() != timezone.utc.utcoffset(date_str):
            return date_str.astimezone()
        return date_str

    def parse(self, date_str: Optional[str]) -> Optional[str]:
        if not date_str:
            return None

        try:
            strategy = self.resolver.resolve(date_str)
            dt = strategy.parse(date_str)
        except Exception:
            return None

        if dt is None:
            return None

        dt = self._convert_into_local_timezone(dt)
        return dt.strftime("%B %d, %Y | %-I:%M %p")