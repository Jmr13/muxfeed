from abc import ABC, abstractmethod
from src.tui.ui_components import UIComponent, TitleBar, EntryList, EntryDetails
    
class UIComponentFactory():
    @staticmethod
    def create_component(component_type, **kwargs) -> UIComponent:
        if component_type == "title_bar":
            return TitleBar(**kwargs)
        elif component_type == "entry_list":
            return EntryList(**kwargs)
        elif component_type == "entry_details":
            return EntryDetails(**kwargs)
        else:
            raise ValueError(f"Unknown component type: {component_type}")