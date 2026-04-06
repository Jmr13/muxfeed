import re
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
            
class RFCFormatTz2Strategy:
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

class DateParser:
    def __init__(self, strategies: Optional[List[DateParseStrategy]] = None):
        # The order of strategies is necessary until we can determine which strategy to use per random date
        # Strategies applicable to datetime with no time zones first
        self.strategies = strategies or [
            ISOFormatStrategy(),
            ISOFormatTzStrategy(),
            RFCFormatStrategy(),
            RFCFormatTz1Strategy(),
            RFCFormatTz2Strategy()
        ]

    def _convertIntoLocalTimeZone(self, date_str: str) -> Optional[str]:
        if date_str.tzinfo and date_str.utcoffset() != timezone.utc.utcoffset(date_str):
            return date_str.astimezone()
        return date_str
            
    import re

    def _getDateParseStrategy(self, date_str: str) -> DateParseStrategy:
        if not date_str:
            return self.strategies[0]  # fallback

        # ISO 8601 with timezone (e.g., 2023-10-05T14:48:00+0000)
        if re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:?\d{2}", date_str):
            return ISOFormatTzStrategy()

        # ISO 8601 without timezone (e.g., 2023-10-05T14:48:00)
        if "T" in date_str:
            return ISOFormatStrategy()

        # RFC with numeric timezone (e.g., Tue, 05 Oct 2023 14:48:00 +0000)
        if re.search(r"[+-]\d{4}", date_str):
            return RFCFormatTz1Strategy()

        # RFC with named timezone (e.g., Tue, 05 Oct 2023 14:48:00 GMT)
        parts = date_str.split()
        if parts and parts[-1] in TZ_OFFSETS:
            return RFCFormatTz2Strategy()

        # RFC without timezone (e.g., Tue, 05 Oct 2023 14:48:00)
        if "," in date_str:
            return RFCFormatStrategy()

        # Fallback: try ISO basic
        return ISOFormatStrategy()

    def parse(self, date_str: Optional[str]) -> Optional[str]:
        if not date_str:
            return None

        if date_str.endswith("Z"):
            date_str = date_str[:-1] + "+0000"

        strategy = self._getDateParseStrategy(date_str)
        dt: Optional[datetime] = strategy.parse(date_str)

        if dt is None:
            for strategy in self.strategies:
                dt = strategy.parse(date_str)
                if dt:
                    break

        if dt is None:
            return None

        dt = self._convertIntoLocalTimeZone(dt)
        return dt.strftime("%B %d, %Y | %-I:%M %p")