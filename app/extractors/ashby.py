from typing import Optional
import json
import httpx
from bs4 import BeautifulSoup

from .base import BaseJobExtractor


class AshbyExtractor(BaseJobExtractor):
    """Extractor for Ashby ATS job listings."""

    @staticmethod
    def can_handle(url: str) -> bool:
        """Check if URL is an Ashby job listing."""
        return "ashbyhq.com" in url or "/jobs.ashbyhq.com/" in url

    def extract(self, url: str) -> Optional[str]:
        """Extract job description from Ashby job listing."""
        try:
            with httpx.Client() as client:
                response = client.get(url, follow_redirects=True, timeout=10.0)
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Ashby embeds job data in JSON-LD schema
            script = soup.find("script", type="application/ld+json")
            if script and script.string:
                try:
                    data = json.loads(script.string)
                    if "description" in data:
                        # Parse HTML in description to plain text
                        desc_soup = BeautifulSoup(data["description"], "html.parser")
                        return desc_soup.get_text(separator="\n", strip=True)
                except json.JSONDecodeError:
                    pass

            return None

        except Exception as e:
            print(f"Error extracting Ashby job: {e}")
            return None
