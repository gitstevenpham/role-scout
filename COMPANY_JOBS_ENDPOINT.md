# Company Engineering Jobs Endpoint

## Overview

The `/company-engineering-jobs` endpoint allows you to find other software engineering job listings from the same company, given a single job listing URL.

## Endpoint

**POST** `/company-engineering-jobs`

## Request

```json
{
  "url": "https://jobs.ashbyhq.com/company/job-id"
}
```

## Response

```json
{
  "company": "Company Name",
  "total_jobs": 10,
  "engineering_jobs": [
    {
      "title": "Senior Software Engineer",
      "url": "https://jobs.ashbyhq.com/company/job-id",
      "location": "San Francisco, CA"
    }
  ]
}
```

## Supported Platforms

- ✅ **Ashby** (ashbyhq.com) - Uses Ashby Postings API
- ✅ **Greenhouse** (greenhouse.io) - Uses Greenhouse Board API
- ⚠️ **Lever** (lever.co) - Implemented, needs testing
- ⚠️ **Workday** (myworkdayjobs.com) - Implemented, needs testing
- ⚠️ **Rippling** (ats.rippling.com) - Implemented, needs testing

## Features

- Automatically detects the ATS platform from the URL
- Fetches all jobs from the company's job board
- Filters for software engineering roles using keyword matching
- Returns up to 20 engineering jobs
- Includes job title, URL, and location (when available)

## Engineering Role Keywords

The endpoint filters for roles containing these keywords:
- software, engineer, developer
- backend, frontend, full-stack, fullstack
- sre, devops
- machine learning, data engineer
- platform, infrastructure
- web, test, programmer, coding

## Usage Examples

### cURL

```bash
# Test with Ashby
curl -X POST http://localhost:8000/company-engineering-jobs \
  -H "Content-Type: application/json" \
  -d '{"url": "https://jobs.ashbyhq.com/st-labs/8cc33e27-fe89-41b8-95e4-9f47540ea8d4"}'

# Test with Greenhouse
curl -X POST http://localhost:8000/company-engineering-jobs \
  -H "Content-Type: application/json" \
  -d '{"url": "https://job-boards.greenhouse.io/anthropic/jobs/5077227008"}'
```

### Python

```python
import httpx

url = "https://jobs.ashbyhq.com/st-labs/8cc33e27-fe89-41b8-95e4-9f47540ea8d4"

with httpx.Client() as client:
    response = client.post(
        "http://localhost:8000/company-engineering-jobs",
        json={"url": url}
    )
    data = response.json()

print(f"Company: {data['company']}")
print(f"Found {data['total_jobs']} engineering jobs")

for job in data['engineering_jobs']:
    print(f"- {job['title']} ({job['location']})")
    print(f"  {job['url']}")
```

## Testing

### Test the extractors directly

```bash
python scripts/test_company_jobs.py
```

### Test the API endpoint

```bash
# Start the server
uvicorn app.main:app --reload

# In another terminal
python scripts/test_api_endpoint.py
```

## Implementation Details

### Architecture

1. **Extractors** (`app/extractors/`)
   - Each ATS has a dedicated extractor class
   - Extractors implement `extract_company_slug()` and `list_company_jobs()`
   - Use APIs when available, fall back to HTML scraping

2. **Factory** (`app/extractors/factory.py`)
   - `list_company_engineering_jobs()` function routes to the appropriate extractor
   - Filters jobs using the engineering role keyword matcher
   - Converts to Pydantic models for API response

3. **Filters** (`app/utils/filters.py`)
   - `is_engineering_role()` function checks job titles against keywords

### API Endpoints Used

- **Ashby**: `https://api.ashbyhq.com/posting-api/job-board/{company}`
- **Greenhouse**: `https://api.greenhouse.io/v1/boards/{company}/jobs`
- **Lever**: `https://api.lever.co/v0/postings/{company}`
- **Rippling**: `https://api.rippling.com/platform/api/ats/v1/board/{board_slug}/jobs`
- **Workday**: HTML scraping (no public API)

## Known Limitations

1. **Rate Limiting**: No rate limiting implemented - may need throttling for production
2. **Workday**: Complex and varies by company, may need adjustments
3. **Location Parsing**: Location formats vary across platforms
4. **Job Limit**: Currently hardcoded to 20 jobs
5. **No Caching**: Fetches from APIs on every request

## Future Improvements

- [ ] Add caching layer for API responses
- [ ] Implement rate limiting
- [ ] Add pagination support
- [ ] Allow customizable job limits
- [ ] Test and verify Lever, Workday, Rippling extractors
- [ ] Add more granular filtering (seniority, remote/on-site, etc.)
- [ ] Add support for more ATS platforms
- [ ] Add retry logic with exponential backoff
- [ ] Better error messages for unsupported platforms

## Error Handling

The endpoint returns an empty list if:
- The platform is not supported
- The company has no jobs posted
- The company has no engineering jobs
- The API is unavailable

Check the server logs for detailed error messages.
