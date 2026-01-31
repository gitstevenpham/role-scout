from typing import Optional
import json
import httpx
from bs4 import BeautifulSoup

from .base import BaseJobExtractor, JobListing


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

    def extract_company_slug(self, url: str) -> Optional[str]:
        """
        Extract company slug from Ashby URL.
        Format: jobs.ashbyhq.com/{company}/{job-id}
        """
        try:
            # Remove protocol and split by /
            parts = url.replace("https://", "").replace("http://", "").split("/")
            # Find jobs.ashbyhq.com index and get next part
            for i, part in enumerate(parts):
                if "ashbyhq.com" in part and i + 1 < len(parts):
                    return parts[i + 1]
            return None
        except Exception:
            return None

    def list_company_jobs(self, url: str) -> tuple[str, list[JobListing]]:
        """
        List all jobs from the same company using Ashby's API.
        Returns (company_name, list_of_jobs).
        """
        company_slug = self.extract_company_slug(url)
        if not company_slug:
            return ("Unknown", [])

        try:
            # Use Ashby's public API
            api_url = f"https://api.ashbyhq.com/posting-api/job-board/{company_slug}"

            with httpx.Client() as client:
                response = client.get(api_url, timeout=10.0)
                response.raise_for_status()
                data = response.json()

            jobs = []
            company_name = company_slug.replace("-", " ").title()

            # Extract jobs from API response
            job_list = data.get("jobs", [])
            for job in job_list:
                title = job.get("title", "")
                job_url = job.get("jobUrl", "")
                location = job.get("location", None)

                # Handle isRemote flag
                if job.get("isRemote"):
                    location = "Remote" if not location else f"{location} (Remote)"

                if title and job_url:
                    jobs.append(JobListing(title=title, url=job_url, location=location))

            return (company_name, jobs)

        except Exception as e:
            print(f"Error listing Ashby company jobs: {e}")
            return (company_slug, [])
