from typing import Optional
import httpx
from bs4 import BeautifulSoup

from .base import BaseJobExtractor, JobListing


class GreenhouseExtractor(BaseJobExtractor):
    """Extractor for Greenhouse ATS job listings."""

    @staticmethod
    def can_handle(url: str) -> bool:
        """Check if URL is a Greenhouse job listing."""
        return "greenhouse.io" in url or "boards.greenhouse.io" in url

    def extract(self, url: str) -> Optional[str]:
        """Extract job description from Greenhouse job listing."""
        try:
            with httpx.Client() as client:
                response = client.get(url, follow_redirects=True, timeout=10.0)
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Greenhouse uses job-post-container class
            job_content = soup.find("div", class_="job-post-container")

            if job_content:
                # Remove application form and other non-job-description elements
                for form in job_content.find_all("form"):
                    form.decompose()
                for app in job_content.find_all("div", {"id": "application"}):
                    app.decompose()

                return job_content.get_text(separator="\n", strip=True)

            return None

        except Exception as e:
            print(f"Error extracting Greenhouse job: {e}")
            return None

    def extract_company_slug(self, url: str) -> Optional[str]:
        """
        Extract company slug from Greenhouse URL.
        Format: job-boards.greenhouse.io/{company}/jobs/{job-id}
        or boards.greenhouse.io/{company}
        """
        try:
            # Remove protocol and split by /
            parts = url.replace("https://", "").replace("http://", "").split("/")
            # Find greenhouse.io index and get next part
            for i, part in enumerate(parts):
                if "greenhouse.io" in part and i + 1 < len(parts):
                    return parts[i + 1]
            return None
        except Exception:
            return None

    def list_company_jobs(self, url: str) -> tuple[str, list[JobListing]]:
        """
        List all jobs from the same company using Greenhouse's API.
        Returns (company_name, list_of_jobs).
        """
        company_slug = self.extract_company_slug(url)
        if not company_slug:
            return ("Unknown", [])

        try:
            # Use Greenhouse's public API
            api_url = f"https://api.greenhouse.io/v1/boards/{company_slug}/jobs"

            with httpx.Client() as client:
                response = client.get(api_url, timeout=10.0)
                response.raise_for_status()
                data = response.json()

            jobs = []
            company_name = company_slug.replace("-", " ").title()

            # Extract jobs from API response
            job_list = data.get("jobs", [])

            # Get company name from first job if available
            if job_list and "company_name" in job_list[0]:
                company_name = job_list[0]["company_name"]

            for job in job_list:
                title = job.get("title", "")
                job_url = job.get("absolute_url", "")

                # Extract location
                location = None
                if "location" in job and job["location"]:
                    location = job["location"].get("name", None)

                if title and job_url:
                    jobs.append(JobListing(title=title, url=job_url, location=location))

            return (company_name, jobs)

        except Exception as e:
            print(f"Error listing Greenhouse company jobs: {e}")
            return (company_slug, [])
