from abc import ABC, abstractmethod
from src.tui.ui_components import TitleBar, EntryList, EntryDetails

class UIComponentFactoryInterface(ABC):
    @abstractmethod
    def create_component(self, component_type, **kwargs):
        pass
    
class UIComponentFactory(UIComponentFactoryInterface):
    @staticmethod
    def create_component(component_type, **kwargs):
        if component_type == "title_bar":
            return TitleBar(**kwargs)
        elif component_type == "entry_list":
            return EntryList(**kwargs)
        elif component_type == "entry_details":
            return EntryDetails(**kwargs)
        else:
            raise ValueError(f"Unknown component type: {component_type}")