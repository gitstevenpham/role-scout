from typing import Optional
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

            # Ashby typically uses specific div classes for job content
            job_content = soup.find("div", class_="ashby-job-posting-brief-info")
            if not job_content:
                job_content = soup.find("div", {"id": "job-description"})

            if not job_content:
                # Fallback: try to find main content area
                job_content = soup.find("main") or soup.find(
                    "div", class_=lambda x: x and "content" in x.lower()
                )

            if job_content:
                return job_content.get_text(separator="\n", strip=True)

            return None

        except Exception as e:
            print(f"Error extracting Ashby job: {e}")
            return None
