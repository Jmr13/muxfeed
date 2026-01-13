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
            dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S")
            return dt
        except ValueError:
            return None

class RFCFormatTz1Strategy(DateParseStrategy):
    def parse(self, date_str: str) -> Optional[datetime]:
        try:
            dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
            return dt
        except Exception:
            return None
            
class RFCFormatTz2Strategy:
    def parse(self, date_str: str) -> Optional[datetime]:
        try:
            parts = date_str.split()
            tz = parts[-1]
            if tz not in TZ_OFFSETS:
                return None
        
            dt = datetime.strptime(" ".join(parts[:-1]), "%a, %d %b %Y %H:%M:%S")
            utc_time = dt - timedelta(hours=TZ_OFFSETS[tz])
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
            
    def _getDateParseStrategy(self, date_str: str) -> DateParseStrategy:
        # TODO: Determine which date parsing strategy to use
        pass

    def parse(self, date_str: Optional[str]) -> Optional[str]:
        if not date_str:
            return None
            
        dt: Optional[datetime] = None
        
        # Apply all strategies until dt has a value
        for strategy in self.strategies:  
            dt = strategy.parse(date_str)  
            if dt is not None:  
                break
            
        # TODO: Apply _getDateParseStrategy to determine which strategy to use
        # strategy = self._getDateParseStrategy(date_str)
        # dt: Optional[datetime] = strategy.parse(date_str)
 
        if dt is None:
            return None
        
        dt = self._convertIntoLocalTimeZone(dt)
        return dt.strftime("%B %d, %Y | %-I:%M %p")