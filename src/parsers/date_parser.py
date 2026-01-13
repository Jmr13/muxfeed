from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from config import TZ_OFFSETS
import time

class DateParseStrategy(ABC):
    @abstractmethod
    def parse(self, date_str: str) -> Optional[datetime]:
        pass

class ISOFormatStrategy(DateParseStrategy):
    def parse(self, date_str: str) -> Optional[datetime]:
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt
        except ValueError:
            return None

class RFC1FormatStrategy(DateParseStrategy):
    def parse(self, date_str: str) -> Optional[datetime]:
        try:
            dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")
            return dt
        except ValueError:
            return None

class RFC2FormatStrategy(DateParseStrategy):
    def parse(self, date_str: str) -> Optional[datetime]:
        try:
            dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
            return dt
        except Exception:
            return None

class CustomTZAbbrStrategy:
    def parse(self, date_str: str) -> Optional[datetime]:
        try:
            *date_parts, tz_abbr = date_str.split()
            date_without_tz = " ".join(date_parts)
            dt = datetime.strptime(date_without_tz, "%a, %d %b %Y %H:%M:%S")
            if tz_abbr not in TZ_OFFSETS:
                return None
            offset_hours = TZ_OFFSETS[tz_abbr]
            dt_utc = dt - timedelta(hours=offset_hours)
            local_offset = -time.timezone / 3600
            dt_local = dt_utc + timedelta(hours=local_offset)
            return dt_local
        except Exception:
            return None
    
class DefaultUTCStrategy(DateParseStrategy):
    def parse(self, date_str: str) -> Optional[datetime]:
        try:
            dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S")
            dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            return None

class DateParser:
    def __init__(self, strategies: Optional[List[DateParseStrategy]] = None):
        # The order of strategies is necessary until we can determine which strategy to use per random date
        self.strategies = strategies or [
            DefaultUTCStrategy(),
            CustomTZAbbrStrategy(),
            ISOFormatStrategy(),
            RFC1FormatStrategy(),
            RFC2FormatStrategy()
        ]

    def _convertIntoLocalTimeZone(self, date_str: str) -> Optional[str]:
        if date_str.tzinfo and date_str.utcoffset() != timezone.utc.utcoffset(date_str):
            return date_str.astimezone()
        return date_str
            
    def _getDateParseStrategy(self, date_str: str) -> DateParseStrategy:
        if "T" in date_str:
            return ISOFormatStrategy()
        elif date_str.endswith("UTC"):
            return RFC2822UTCStrategy()
        elif "+" in date_str or "-" in date_str[-5:]:
            return RFC2822OffsetStrategy()
        elif date_str[-3:].isalpha():
            return CustomTZAbbrStrategy()
        else:
            return DefaultUTCStrategy()

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