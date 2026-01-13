from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional, List
from config import TZ_MAP

class DateParseStrategy(ABC):
    @abstractmethod
    def parse(self, date_str: str) -> Optional[datetime]:
        pass

class ISOFormatStrategy(DateParseStrategy):
    def parse(self, date_str: str) -> Optional[datetime]:
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            return None

class RFC2822UTCStrategy(DateParseStrategy):
    def parse(self, date_str: str) -> Optional[datetime]:
        try:
            dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return None

class RFC2822OffsetStrategy(DateParseStrategy):
    def parse(self, date_str: str) -> Optional[datetime]:
        try:
            return datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
        except ValueError:
            return None

class CustomTZAbbrStrategy(DateParseStrategy):
    def parse(self, date_str: str) -> Optional[datetime]:
        try:
            dt_part, tz_abbr = date_str.rsplit(" ", 1)
            dt = datetime.strptime(dt_part, "%a, %d %b %Y %H:%M:%S")
            if tz_abbr in TZ_MAP:
                dt = dt.replace(tzinfo=TZ_MAP[tz_abbr])
            return dt
        except Exception:
            return None

class DefaultUTCStrategy(DateParseStrategy):
    def parse(self, date_str: str) -> Optional[datetime]:
        try:
            dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return None

class DateParser:
    def __init__(self, strategies: Optional[List[DateParseStrategy]] = None):
        self.strategies = strategies or [
            ISOFormatStrategy(),
            RFC2822UTCStrategy(),
            RFC2822OffsetStrategy(),
            CustomTZAbbrStrategy(),
            DefaultUTCStrategy()
        ]
    
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
        for strategy in self.strategies:  
            dt = strategy.parse(date_str)  
            if dt is not None:  
                break
            
        # TODO: Apply _getDateParseStrategy to determine which strategy to use
        # strategy = self._getDateParseStrategy(date_str)
        # dt: Optional[datetime] = strategy.parse(date_str)
 
        if dt is None:
            return None

        dt_utc = dt.astimezone(timezone.utc)
        return dt_utc.strftime("%B %-d, %Y | %-I:%M %p")