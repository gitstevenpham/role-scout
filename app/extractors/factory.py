from typing import Optional

from .ashby import AshbyExtractor
from .greenhouse import GreenhouseExtractor
from .linkedin import LinkedInExtractor
from .base import BaseJobExtractor


EXTRACTORS: list[type[BaseJobExtractor]] = [
    AshbyExtractor,
    GreenhouseExtractor,
    LinkedInExtractor,
]


def extract_job_description(url: str) -> Optional[str]:
    """
    Extract job description from a URL by detecting the appropriate ATS.

    Args:
        url: The job listing URL

    Returns:
        Extracted job description text, or None if extraction fails
    """
    for extractor_class in EXTRACTORS:
        if extractor_class.can_handle(url):
            extractor = extractor_class()
            return extractor.extract(url)

    return None
