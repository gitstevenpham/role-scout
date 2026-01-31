from typing import Optional
import re
import httpx
from bs4 import BeautifulSoup

from .base import BaseJobExtractor, JobListing


class WorkdayExtractor(BaseJobExtractor):
    """Extractor for Workday ATS job listings."""

    @staticmethod
    def can_handle(url: str) -> bool:
        """Check if URL is a Workday job listing."""
        return "myworkdayjobs.com" in url

    def extract(self, url: str) -> Optional[str]:
        """Extract job description from Workday job listing."""
        try:
            with httpx.Client() as client:
                response = client.get(url, follow_redirects=True, timeout=10.0)
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Workday uses various selectors
            job_content = soup.find("div", {"data-automation-id": "jobPostingDescription"})
            if not job_content:
                job_content = soup.find("div", class_="jobDescription")
            if not job_content:
                # Try to find by aria-label
                job_content = soup.find("div", {"aria-label": "Job Description"})

            if job_content:
                return job_content.get_text(separator="\n", strip=True)

            return None

        except Exception as e:
            print(f"Error extracting Workday job: {e}")
            return None

    def extract_company_slug(self, url: str) -> Optional[str]:
        """
        Extract company slug from Workday URL.
        Format: {company}.wd{X}.myworkdayjobs.com/...
        """
        try:
            # Extract subdomain pattern
            match = re.search(r"([^.]+)\.wd\d+\.myworkdayjobs\.com", url)
            if match:
                return match.group(1)
            return None
        except Exception:
            return None

    def list_company_jobs(self, url: str) -> tuple[str, list[JobListing]]:
        """
        List all jobs from the same company by scraping the job board.
        Returns (company_name, list_of_jobs).
        """
        company_slug = self.extract_company_slug(url)
        if not company_slug:
            return ("Unknown", [])

        try:
            # Try to find the job board URL from the original URL
            # Workday URLs typically have format: {company}.wd{X}.myworkdayjobs.com/{board_name}/...
            match = re.search(
                r"(https?://[^.]+\.wd\d+\.myworkdayjobs\.com/[^/]+)", url
            )
            if not match:
                # Fallback: construct a generic board URL
                match_wd = re.search(r"\.wd(\d+)\.", url)
                wd_num = match_wd.group(1) if match_wd else "1"
                board_url = f"https://{company_slug}.wd{wd_num}.myworkdayjobs.com/{company_slug}"
            else:
                board_url = match.group(1)

            with httpx.Client() as client:
                response = client.get(board_url, follow_redirects=True, timeout=10.0)
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            jobs = []
            company_name = company_slug.replace("-", " ").title()

            # Workday uses li elements with data-automation-id="jobPostingItem"
            job_items = soup.find_all("li", {"data-automation-id": "jobPostingItem"})

            for item in job_items:
                # Find the link and title
                link = item.find("a", {"data-automation-id": "jobTitle"})
                if link:
                    title = link.get_text(strip=True)
                    job_url = link.get("href", "")

                    # Make URL absolute if it's relative
                    if job_url.startswith("/"):
                        base_url = re.search(r"(https?://[^/]+)", board_url)
                        if base_url:
                            job_url = base_url.group(1) + job_url

                    # Extract location if available
                    location_elem = item.find(
                        "dd", {"data-automation-id": "location"}
                    )
                    location = (
                        location_elem.get_text(strip=True) if location_elem else None
                    )

                    if title and job_url:
                        jobs.append(
                            JobListing(title=title, url=job_url, location=location)
                        )

            return (company_name, jobs)

        except Exception as e:
            print(f"Error listing Workday company jobs: {e}")
            return (company_slug, [])
