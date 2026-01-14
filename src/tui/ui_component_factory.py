from abc import ABC, abstractmethod
from src.tui.ui_components import TitleBar, EntryList, EntryDetails

class UIComponentFactoryInterface(ABC):
    @abstractmethod
    def create_component(self, component_type, **kwargs):
        pass
    
class UIComponentFactory:
    @staticmethod
    def create_component(component_type, **kwargs):
        if component_type == "title_bar":
            return TitleBar(kwargs.get("text", ""))
        elif component_type == "entry_list":
            return EntryList(
                kwargs.get("entries", []),
                kwargs.get("selected", 0),
                kwargs.get("start_index", 0)
            )
        elif component_type == "entry_details":
            return EntryDetails(kwargs.get("entry"))
        else:
            raise ValueError(f"Unknown component type: {component_type}")