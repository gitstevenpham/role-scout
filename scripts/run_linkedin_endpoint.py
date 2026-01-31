#!/usr/bin/env python3
"""Script to test the LinkedIn company jobs endpoint."""

import httpx
import json


def run_linkedin_company_jobs():
    """Test the /linkedin-company-jobs endpoint with a LinkedIn URL."""

    # API endpoint
    url = "http://localhost:8000/linkedin-company-jobs"

    # LinkedIn job URL
    linkedin_url = "https://www.linkedin.com/jobs/collections/recommended/?currentJobId=4323227137&start=48"

    # Request payload
    payload = {
        "url": linkedin_url
    }

    print(f"Testing endpoint: {url}")
    print(f"LinkedIn URL: {linkedin_url}")
    print("-" * 80)

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, json=payload)

            print(f"Status Code: {response.status_code}")
            print("-" * 80)

            if response.status_code == 200:
                data = response.json()
                print(f"Company: {data['company']}")
                print(f"Total Engineering Jobs: {data['total_jobs']}")
                print("-" * 80)
                print("\nEngineering Jobs:")
                for i, job in enumerate(data['engineering_jobs'], 1):
                    print(f"\n{i}. {job['title']}")
                    print(f"   URL: {job['url']}")
                    print(f"   Location: {job.get('location', 'N/A')}")
            else:
                print("Error Response:")
                print(json.dumps(response.json(), indent=2))

    except httpx.ConnectError:
        print("ERROR: Could not connect to the API server.")
        print("Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    run_linkedin_company_jobs()
