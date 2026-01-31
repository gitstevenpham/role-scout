from abc import ABC, abstractmethod
from typing import Optional


class JobListing:
    """Simple job listing data class."""

    def __init__(self, title: str, url: str, location: str | None = None):
        self.title = title
        self.url = url
        self.location = location


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

    def extract_company_slug(self, url: str) -> Optional[str]:
        """
        Extract company identifier from job URL.
        Returns None if cannot extract.
        """
        return None

    def list_company_jobs(self, url: str) -> tuple[str, list[JobListing]]:
        """
        List all jobs from the same company.
        Returns (company_name, list_of_jobs).
        """
        return ("Unknown", [])
