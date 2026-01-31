from typing import Optional
import httpx
from bs4 import BeautifulSoup

from .base import BaseJobExtractor, JobListing


class RipplingExtractor(BaseJobExtractor):
    """Extractor for Rippling ATS job listings."""

    @staticmethod
    def can_handle(url: str) -> bool:
        """Check if URL is a Rippling job listing."""
        return "ats.rippling.com" in url

    def extract(self, url: str) -> Optional[str]:
        """Extract job description from Rippling job listing."""
        try:
            with httpx.Client() as client:
                response = client.get(url, follow_redirects=True, timeout=10.0)
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Rippling uses various class names, try to find the main content
            job_content = soup.find("div", class_="job-description")
            if not job_content:
                job_content = soup.find("div", {"data-testid": "job-description"})
            if not job_content:
                # Try to find any main content div
                job_content = soup.find("main")

            if job_content:
                # Remove application forms
                for form in job_content.find_all("form"):
                    form.decompose()

                return job_content.get_text(separator="\n", strip=True)

            return None

        except Exception as e:
            print(f"Error extracting Rippling job: {e}")
            return None

    def extract_company_slug(self, url: str) -> Optional[str]:
        """
        Extract company slug from Rippling URL.
        Format: ats.rippling.com/{board_slug}/jobs/{job-id}
        """
        try:
            # Remove protocol and split by /
            parts = url.replace("https://", "").replace("http://", "").split("/")
            # Find ats.rippling.com index and get next part
            for i, part in enumerate(parts):
                if "ats.rippling.com" in part and i + 1 < len(parts):
                    return parts[i + 1]
            return None
        except Exception:
            return None

    def list_company_jobs(self, url: str) -> tuple[str, list[JobListing]]:
        """
        List all jobs from the same company using Rippling Job Board API.
        Returns (company_name, list_of_jobs).
        """
        board_slug = self.extract_company_slug(url)
        if not board_slug:
            return ("Unknown", [])

        try:
            # Use Rippling's public API with cursor-based pagination
            api_url = f"https://api.rippling.com/platform/api/ats/v1/board/{board_slug}/jobs"

            jobs = []
            company_name = board_slug.replace("-", " ").title()
            cursor = None

            with httpx.Client() as client:
                # Fetch all pages
                while True:
                    params = {"limit": 100}
                    if cursor:
                        params["cursor"] = cursor

                    response = client.get(api_url, params=params, timeout=10.0)
                    response.raise_for_status()
                    data = response.json()

                    # Extract jobs from response
                    job_list = data.get("jobs", [])
                    for job in job_list:
                        title = job.get("title", "")
                        job_id = job.get("id", "")
                        location = job.get("location", {}).get("name", None)
                        job_url = f"https://ats.rippling.com/{board_slug}/jobs/{job_id}"

                        if title and job_id:
                            jobs.append(
                                JobListing(title=title, url=job_url, location=location)
                            )

                    # Check for next page
                    cursor = data.get("nextCursor")
                    if not cursor:
                        break

            return (company_name, jobs)

        except Exception as e:
            print(f"Error listing Rippling company jobs: {e}")
            return (board_slug, [])
