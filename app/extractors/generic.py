from typing import Optional
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup
from bs4.element import Tag

from .base import BaseJobExtractor, JobListing


class GenericExtractor(BaseJobExtractor):
    """
    Fallback extractor for job listings when no specific ATS is detected.
    Uses best-effort heuristics to extract job descriptions from any webpage.
    """

    @staticmethod
    def can_handle(url: str) -> bool:
        """
        This is a catch-all extractor, so it can handle any URL.
        Should be registered last in the extractor list.
        """
        return True

    def extract(self, url: str) -> Optional[str]:
        """
        Extract job description using generic HTML parsing strategies.
        Tries multiple heuristics to find the most relevant content.
        """
        try:
            with httpx.Client() as client:
                response = client.get(url, follow_redirects=True, timeout=10.0)
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Remove unwanted elements that are typically not part of job descriptions
            self._remove_noise(soup)

            # Try multiple strategies in order of specificity
            content = (
                self._try_semantic_tags(soup)
                or self._try_common_class_patterns(soup)
                or self._try_main_content(soup)
                or self._try_largest_text_block(soup)
            )

            if content:
                return self._clean_text(content)

            return None

        except Exception as e:
            print(f"Error in generic job extraction: {e}")
            return None

    def _remove_noise(self, soup: BeautifulSoup) -> None:
        """Remove common non-content elements."""
        # Remove scripts, styles, navigation, headers, footers
        for tag in soup.find_all(
            [
                "script",
                "style",
                "nav",
                "header",
                "footer",
                "iframe",
                "noscript",
            ]
        ):
            tag.decompose()

        # Remove common utility elements
        noise_words = [
            "nav",
            "menu",
            "sidebar",
            "footer",
            "header",
            "cookie",
            "banner",
            "modal",
            "popup",
            "ad",
        ]
        for element in soup.find_all(
            class_=lambda x: isinstance(x, str)
            and any(word in x.lower() for word in noise_words)
        ):
            element.decompose()

    def _try_semantic_tags(self, soup: BeautifulSoup) -> Optional[str]:
        """Try HTML5 semantic tags that might contain job descriptions."""
        # Try <article> tag - often used for main content
        article = soup.find("article")
        if article and isinstance(article, Tag) and self._has_substantial_text(article):
            return article.get_text(separator="\n", strip=True)

        # Try <main> tag
        main = soup.find("main")
        if main and isinstance(main, Tag) and self._has_substantial_text(main):
            return main.get_text(separator="\n", strip=True)

        return None

    def _try_common_class_patterns(self, soup: BeautifulSoup) -> Optional[str]:
        """Try common CSS class/id patterns used for job descriptions."""
        # Common patterns in class names and IDs
        patterns = [
            "job-description",
            "job-content",
            "job-detail",
            "job-posting",
            "position-description",
            "role-description",
            "description",
            "posting",
            "job-body",
            "content-main",
            "post-content",
            "vacancy-description",
        ]

        for pattern in patterns:
            # Try class names
            element = soup.find(class_=lambda x: isinstance(x, str) and pattern in x.lower())
            if element and isinstance(element, Tag) and self._has_substantial_text(element):
                return element.get_text(separator="\n", strip=True)

            # Try IDs
            element = soup.find(id=lambda x: isinstance(x, str) and pattern in x.lower())
            if element and isinstance(element, Tag) and self._has_substantial_text(element):
                return element.get_text(separator="\n", strip=True)

        return None

    def _try_main_content(self, soup: BeautifulSoup) -> Optional[str]:
        """Try to find main content area by common container patterns."""
        # Try common container classes
        content_words = ["content", "container", "main"]
        containers = soup.find_all(
            ["div", "section"],
            class_=lambda x: isinstance(x, str)
            and any(word in x.lower() for word in content_words),
        )

        # Find the container with the most text
        best_container = None
        max_length = 0

        for container in containers:
            if not isinstance(container, Tag):
                continue
            text = container.get_text(separator="\n", strip=True)
            text_length = len(text)

            if text_length > max_length and self._has_substantial_text(container):
                max_length = text_length
                best_container = container

        if best_container:
            return best_container.get_text(separator="\n", strip=True)

        return None

    def _try_largest_text_block(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Last resort: find the largest coherent block of text on the page.
        Looks for divs or sections with substantial text content.
        """
        # Look at all divs and sections
        candidates = soup.find_all(["div", "section", "article"])

        best_element = None
        max_length = 0

        for element in candidates:
            # Skip if it's too nested (likely contains other candidates)
            if len(element.find_all(["div", "section"])) > 10:
                continue

            text = element.get_text(separator="\n", strip=True)
            text_length = len(text)

            # Must have at least 500 characters to be considered
            if text_length > max_length and text_length > 500:
                max_length = text_length
                best_element = element

        if best_element:
            return best_element.get_text(separator="\n", strip=True)

        return None

    def _has_substantial_text(self, element: Tag) -> bool:
        """Check if an element has enough text to be a job description."""
        text = element.get_text(separator=" ", strip=True)
        # Job descriptions are typically at least 200 characters
        return len(text) > 200

    def _clean_text(self, text: str) -> str:
        """Clean up extracted text."""
        # Remove excessive whitespace
        lines = [line.strip() for line in text.split("\n")]
        # Remove empty lines
        lines = [line for line in lines if line]
        # Join with single newlines
        return "\n".join(lines)

    def extract_company_slug(self, url: str) -> Optional[str]:
        """
        Extract company identifier from URL.
        For generic URLs, uses the domain name.
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            # Remove common prefixes
            domain = domain.replace("www.", "").replace("careers.", "").replace("jobs.", "")
            # Get the main domain name (before TLD)
            return domain.split(".")[0] if domain else None
        except Exception:
            return None

    def list_company_jobs(self, url: str) -> tuple[str, list[JobListing]]:
        """
        Best-effort attempt to list all jobs from the same company.
        Tries to find a job listing page and extract job links.
        Returns (company_name, list_of_jobs).
        """
        try:
            parsed = urlparse(url)
            base_domain = f"{parsed.scheme}://{parsed.netloc}"

            # Try to find the jobs listing page
            # Common patterns: /jobs, /careers, /positions, /opportunities
            jobs_page_url = self._find_jobs_listing_page(url, base_domain)

            if not jobs_page_url:
                return (self.extract_company_slug(url) or "Unknown", [])

            # Fetch the jobs listing page
            with httpx.Client() as client:
                response = client.get(jobs_page_url, follow_redirects=True, timeout=10.0)
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract company name
            company_name = self._extract_company_name(soup, url)

            # Find all job links
            jobs = self._extract_job_listings(soup, base_domain, url)

            return (company_name, jobs)

        except Exception as e:
            print(f"Error listing company jobs: {e}")
            return (self.extract_company_slug(url) or "Unknown", [])

    def _find_jobs_listing_page(self, original_url: str, base_domain: str) -> Optional[str]:
        """
        Try to find the jobs listing page from a job detail URL.
        Returns the URL of the listing page, or None if not found.
        """
        parsed = urlparse(original_url)
        path = parsed.path

        # Common patterns in job detail URLs
        # Example: /positions/123456/ -> /positions/
        # Example: /careers/jobs/123/ -> /careers/ or /careers/jobs/
        # Example: /jobs/engineering/senior-engineer-123 -> /jobs/

        common_patterns = [
            "position",
            "job",
            "career",
            "opening",
            "opportunity",
            "role",
            "vacancy",
        ]

        path_parts = [p for p in path.split("/") if p]

        # Try to find a jobs-related segment
        for i, part in enumerate(path_parts):
            if any(pattern in part.lower() for pattern in common_patterns):
                # Try the path up to and including this segment
                listing_path = "/" + "/".join(path_parts[: i + 1]) + "/"
                return base_domain + listing_path

        # Fallback: try common paths
        for pattern in ["positions", "jobs", "careers", "opportunities"]:
            test_url = f"{base_domain}/{pattern}/"
            try:
                with httpx.Client() as client:
                    response = client.head(test_url, follow_redirects=True, timeout=5.0)
                    if response.status_code == 200:
                        return test_url
            except Exception:
                continue

        return None

    def _extract_company_name(self, soup: BeautifulSoup, url: str) -> str:
        """Extract company name from the page or URL."""
        # Try to find company name in common places
        # Check meta tags
        og_site_name = soup.find("meta", property="og:site_name")
        if og_site_name and isinstance(og_site_name, Tag):
            content = og_site_name.get("content")
            if content and isinstance(content, str):
                return content

        # Check title tag
        title = soup.find("title")
        if title and isinstance(title, Tag):
            title_text = title.get_text(strip=True)
            # Common patterns: "Company Name - Careers" or "Careers at Company Name"
            for separator in [" - ", " | ", " at "]:
                if separator in title_text:
                    parts = title_text.split(separator)
                    # Return the first part if it's not "Careers" or "Jobs"
                    for part in parts:
                        if part and part.lower() not in ["careers", "jobs", "positions"]:
                            return part

        # Fallback to domain name
        slug = self.extract_company_slug(url)
        return slug.replace("-", " ").title() if slug else "Unknown"

    def _extract_job_listings(
        self, soup: BeautifulSoup, base_domain: str, original_url: str
    ) -> list[JobListing]:
        """Extract job listings from the page."""
        jobs = []
        seen_urls = set()

        # Find all links on the page
        all_links = soup.find_all("a", href=True)

        # Determine the pattern for job URLs based on the original URL
        parsed_original = urlparse(original_url)
        job_url_pattern = self._determine_job_url_pattern(parsed_original.path)

        for link in all_links:
            href = link.get("href")
            if not href or not isinstance(href, str):
                continue

            # Make URL absolute
            absolute_url = urljoin(base_domain, href)

            # Check if this looks like a job detail URL
            if not self._looks_like_job_url(absolute_url, job_url_pattern):
                continue

            # Avoid duplicate URLs
            if absolute_url in seen_urls:
                continue

            # Get job title from link text
            title = link.get_text(strip=True)
            if not title or len(title) < 3:
                continue

            # Skip if title looks like navigation
            if title.lower() in ["jobs", "careers", "all jobs", "view all", "more"]:
                continue

            # Try to extract location
            location = self._extract_location_near_link(link)

            jobs.append(JobListing(title=title, url=absolute_url, location=location))
            seen_urls.add(absolute_url)

        return jobs

    def _determine_job_url_pattern(self, original_path: str) -> str:
        """
        Determine the URL pattern for job detail pages.
        Returns a pattern string like 'positions' or 'jobs'.
        """
        common_patterns = [
            "position",
            "job",
            "career",
            "opening",
            "opportunity",
            "role",
            "vacancy",
        ]

        path_lower = original_path.lower()
        for pattern in common_patterns:
            if pattern in path_lower:
                return pattern

        return "job"  # Default fallback

    def _looks_like_job_url(self, url: str, pattern: str) -> bool:
        """Check if a URL looks like a job detail page."""
        url_lower = url.lower()

        # Must contain the pattern
        if pattern not in url_lower:
            return False

        # Should have some identifier (number or slug)
        # Typically job URLs have: /jobs/123 or /jobs/engineer-senior
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split("/") if p]

        # Need at least 2 parts (e.g., ['jobs', '123'])
        if len(path_parts) < 2:
            return False

        # The last part should look like an ID or slug
        last_part = path_parts[-1]
        # Check if it's a number or a slug (has hyphens/underscores)
        if last_part.isdigit() or "-" in last_part or "_" in last_part:
            return True

        return False

    def _extract_location_near_link(self, link: Tag) -> Optional[str]:
        """Try to extract location information near a job link."""
        # Look in the same parent container
        parent = link.parent
        if not parent or not isinstance(parent, Tag):
            return None

        # Look for elements with 'location' in class name
        location_elem = parent.find(
            class_=lambda x: isinstance(x, str) and "location" in x.lower()
        )
        if location_elem and isinstance(location_elem, Tag):
            return location_elem.get_text(strip=True)

        # Look for common location indicators nearby
        for sibling in parent.find_all(["span", "div", "p"]):
            if not isinstance(sibling, Tag):
                continue
            text = sibling.get_text(strip=True)
            # Common location patterns
            if any(
                indicator in text.lower()
                for indicator in ["remote", "hybrid", "onsite", "office"]
            ):
                return text

        return None