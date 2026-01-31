from typing import Optional
import re
import httpx
from bs4 import BeautifulSoup

from .base import BaseJobExtractor


class LinkedInExtractor(BaseJobExtractor):
    """Extractor for LinkedIn job listings."""

    @staticmethod
    def can_handle(url: str) -> bool:
        """Check if URL is a LinkedIn job listing."""
        return "linkedin.com/jobs" in url

    def _normalize_url(self, url: str) -> Optional[str]:
        """
        Normalize LinkedIn URL to view/{id} format.

        Handles various LinkedIn job URL formats:
        - /jobs/view/123456
        - /jobs/collections/recommended/?currentJobId=123456
        - Any other format with a job ID
        """
        # Try to find job ID in various formats
        patterns = [
            r"/jobs/view/(\d+)",
            r"currentJobId=(\d+)",
            r"jobId=(\d+)",
            r"/jobs/(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                job_id = match.group(1)
                return f"https://www.linkedin.com/jobs/view/{job_id}"

        return None

    def get_company_name(self, url: str) -> Optional[str]:
        """
        Extract company name from LinkedIn job listing.

        Args:
            url: LinkedIn job URL

        Returns:
            Company name or None if extraction fails
        """
        try:
            normalized_url = self._normalize_url(url)
            if not normalized_url:
                return None

            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }

            with httpx.Client() as client:
                response = client.get(
                    normalized_url, headers=headers, follow_redirects=True, timeout=10.0
                )
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Try to find company name in various locations
            # Method 1: Look for company link/name in the job card
            company_link = soup.find("a", class_=lambda x: x and "topcard__org-name-link" in str(x))
            if company_link:
                return company_link.get_text(strip=True)

            # Method 2: Look for subtitle with company info
            company_subtitle = soup.find("span", class_=lambda x: x and "topcard__flavor" in str(x))
            if company_subtitle:
                return company_subtitle.get_text(strip=True)

            # Method 3: Look for any element with company name pattern
            company_div = soup.find("div", class_=lambda x: x and "company" in str(x).lower())
            if company_div:
                return company_div.get_text(strip=True)

            return None

        except Exception as e:
            print(f"Error extracting company name from LinkedIn: {e}")
            return None

    def extract(self, url: str) -> Optional[str]:
        """Extract job description from LinkedIn job listing."""
        try:
            # Normalize URL to consistent format
            normalized_url = self._normalize_url(url)
            if not normalized_url:
                print(f"Could not extract job ID from URL: {url}")
                return None

            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }

            with httpx.Client() as client:
                response = client.get(
                    normalized_url, headers=headers, follow_redirects=True, timeout=10.0
                )
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # LinkedIn uses specific classes for job description
            job_content = soup.find("div", class_="description__text")
            if not job_content:
                job_content = soup.find(
                    "div", class_=lambda x: x and "show-more-less-html__markup" in str(x)
                )

            if not job_content:
                # Try alternative selectors
                job_content = soup.find("section", class_=lambda x: x and "description" in str(x))

            if job_content:
                return job_content.get_text(separator="\n", strip=True)

            return None

        except Exception as e:
            print(f"Error extracting LinkedIn job: {e}")
            return None
