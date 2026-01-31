"""
Job Extractor Test Runner
Run this script directly in PyCharm to test job extractors.
"""

from extractors import extract_job_description


def run_url(platform: str, url: str):
    """Test extraction for a single URL."""
    print("\n" + "=" * 80)
    print(f"Testing: {platform}")
    print(f"URL: {url}")
    print("=" * 80)

    try:
        content = extract_job_description(url)

        if content:
            print(f"\n✓ SUCCESS - Extracted {len(content)} characters")

            # Show first 500 characters
            print(f"\n--- First 500 characters ---")
            print(content[:500])
            print("..." if len(content) > 500 else "")

            # Statistics
            lines = content.split("\n")
            non_empty = [l for l in lines if l.strip()]

            print(f"\n--- Statistics ---")
            print(f"Total characters: {len(content)}")
            print(f"Total lines: {len(lines)}")
            print(f"Non-empty lines: {len(non_empty)}")

            return True
        else:
            print("\n✗ FAILED - No content extracted")
            print("Possible reasons:")
            print("  • Invalid or inaccessible URL")
            print("  • Page structure doesn't match selectors")
            print("  • Authentication required")
            return False

    except Exception as e:
        print(f"\n✗ ERROR - {type(e).__name__}: {e}")
        return False


def main():
    """Run all extraction tests."""
    print("\n" + "=" * 80)
    print("JOB EXTRACTOR TEST RUNNER")
    print("=" * 80)

    # Test URLs
    test_cases = [
        ("Ashby (ST Labs)", "https://jobs.ashbyhq.com/st-labs/8cc33e27-fe89-41b8-95e4-9f47540ea8d4"),
        ("Greenhouse (Anthropic)", "https://job-boards.greenhouse.io/anthropic/jobs/5077227008"),
        ("LinkedIn", "https://www.linkedin.com/jobs/collections/recommended/?currentJobId=4265031115"),
    ]

    results = []
    for platform, url in test_cases:
        success = run_url(platform, url)
        results.append((platform, success))

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for platform, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} - {platform}")

    print(f"\nTotal: {passed}/{total} passed")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
