from typing import Optional
import httpx
from bs4 import BeautifulSoup

from .base import BaseJobExtractor, JobListing


class LeverExtractor(BaseJobExtractor):
    """Extractor for Lever ATS job listings."""

    @staticmethod
    def can_handle(url: str) -> bool:
        """Check if URL is a Lever job listing."""
        return "jobs.lever.co" in url

    def extract(self, url: str) -> Optional[str]:
        """Extract job description from Lever job listing."""
        try:
            with httpx.Client() as client:
                response = client.get(url, follow_redirects=True, timeout=10.0)
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Lever uses posting-page class for the main job content
            job_content = soup.find("div", class_="posting-page")

            if job_content:
                # Remove application form
                for form in job_content.find_all("div", class_="application"):
                    form.decompose()

                return job_content.get_text(separator="\n", strip=True)

            return None

        except Exception as e:
            print(f"Error extracting Lever job: {e}")
            return None

    def extract_company_slug(self, url: str) -> Optional[str]:
        """
        Extract company slug from Lever URL.
        Format: jobs.lever.co/{company}/{job-id}
        """
        try:
            # Remove protocol and split by /
            parts = url.replace("https://", "").replace("http://", "").split("/")
            # Find jobs.lever.co index and get next part
            for i, part in enumerate(parts):
                if "jobs.lever.co" in part and i + 1 < len(parts):
                    return parts[i + 1]
            return None
        except Exception:
            return None

    def list_company_jobs(self, url: str) -> tuple[str, list[JobListing]]:
        """
        List all jobs from the same company using Lever Postings API.
        Returns (company_name, list_of_jobs).
        """
        company_slug = self.extract_company_slug(url)
        if not company_slug:
            return ("Unknown", [])

        try:
            # Use Lever's public API
            api_url = f"https://api.lever.co/v0/postings/{company_slug}"

            with httpx.Client() as client:
                response = client.get(api_url, timeout=10.0)
                response.raise_for_status()
                data = response.json()

            jobs = []
            company_name = company_slug.replace("-", " ").title()

            for posting in data:
                title = posting.get("text", "")
                posting_url = posting.get("hostedUrl", "")
                location = posting.get("categories", {}).get("location", None)

                if title and posting_url:
                    jobs.append(JobListing(title=title, url=posting_url, location=location))

            # Try to get a better company name from the first job if available
            if data and "additional" in data[0]:
                company_name = data[0].get("additional", company_slug)

            return (company_name, jobs)

        except Exception as e:
            print(f"Error listing Lever company jobs: {e}")
            return (company_slug, [])
