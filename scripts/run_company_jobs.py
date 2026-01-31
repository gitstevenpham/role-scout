"""Test script for company job listings extraction."""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.extractors.factory import list_company_engineering_jobs


def run_extractor(name: str, url: str):
    """Test a single extractor with a URL."""
    print(f"\n{'=' * 80}")
    print(f"Testing {name}")
    print(f"URL: {url}")
    print(f"{'=' * 80}")

    try:
        company, jobs = list_company_engineering_jobs(url)
        print(f"\n✓ Company: {company}")
        print(f"✓ Found {len(jobs)} engineering jobs")

        if jobs:
            print("\nFirst 5 jobs:")
            for i, job in enumerate(jobs[:5], 1):
                print(f"\n{i}. {job.title}")
                print(f"   URL: {job.url}")
                if job.location:
                    print(f"   Location: {job.location}")
        else:
            print("\n⚠ No engineering jobs found")

    except Exception as e:
        print(f"\n✗ Error: {e}")


def main():
    """Run tests for all extractors."""
    print("Testing Company Job Listings Extraction")
    print("=" * 80)

    # Test cases for each platform
    test_cases = [
        # (
        #     "Ashby",
        #     "https://jobs.ashbyhq.com/st-labs/8cc33e27-fe89-41b8-95e4-9f47540ea8d4",
        # ),
        (
            "Greenhouse",
            "https://job-boards.greenhouse.io/anthropic/jobs/5077227008",
        ),
        # Add more test cases as needed:
        # ("Lever", "https://jobs.lever.co/company/job-id"),
        # ("Workday", "https://company.wd1.myworkdayjobs.com/..."),
        # ("Rippling", "https://ats.rippling.com/board/jobs/job-id"),
    ]

    for name, url in test_cases:
        run_extractor(name, url)

    print(f"\n{'=' * 80}")
    print("Testing complete!")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()
