from abc import ABC, abstractmethod
import threading

class SpeechEngine(ABC):
    @abstractmethod
    def speak(self, text: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError