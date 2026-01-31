from abc import ABC, abstractmethod
from typing import Optional


class BaseJobExtractor(ABC):
    @abstractmethod
    def extract(self, url: str) -> Optional[str]:
        """
        Extract job description from a URL.
        Returns None if extraction fails.
        """
        pass

    @staticmethod
    @abstractmethod
    def can_handle(url: str) -> bool:
        """Check if this extractor can handle the given URL."""
        pass
