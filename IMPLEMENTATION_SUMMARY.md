# Implementation Summary: Company Engineering Jobs Endpoint

## What Was Implemented

A new API endpoint `/company-engineering-jobs` that takes a job listing URL and returns up to 20 other software engineering jobs from the same company.

## ✅ Completed Components

### 1. **Filters Utility** (`app/utils/filters.py`)
- Created `is_engineering_role()` function
- Filters job titles based on engineering-related keywords
- Keywords include: software, engineer, developer, backend, frontend, devops, etc.

### 2. **New Extractors**

#### Lever Extractor (`app/extractors/lever.py`)
- Handles `jobs.lever.co` URLs
- Uses Lever Postings API: `https://api.lever.co/v0/postings/{company}`
- Extracts company slug from URL path
- ⚠️ **Status**: Implemented but needs testing with real Lever URLs

#### Rippling Extractor (`app/extractors/rippling.py`)
- Handles `ats.rippling.com` URLs
- Uses Rippling Job Board API with cursor-based pagination
- API: `https://api.rippling.com/platform/api/ats/v1/board/{board_slug}/jobs`
- ⚠️ **Status**: Implemented but needs testing with real Rippling URLs

#### Workday Extractor (`app/extractors/workday.py`)
- Handles `myworkdayjobs.com` URLs
- Uses HTML scraping (no public API)
- Extracts company slug from subdomain pattern
- ⚠️ **Status**: Implemented but needs testing with real Workday URLs

### 3. **Enhanced Existing Extractors**

#### Ashby Extractor (`app/extractors/ashby.py`)
- ✅ Added `extract_company_slug()` method
- ✅ Added `list_company_jobs()` method using Ashby API
- ✅ API: `https://api.ashbyhq.com/posting-api/job-board/{company}`
- ✅ **Status**: Tested and working with St Labs

#### Greenhouse Extractor (`app/extractors/greenhouse.py`)
- ✅ Added `extract_company_slug()` method
- ✅ Added `list_company_jobs()` method using Greenhouse API
- ✅ API: `https://api.greenhouse.io/v1/boards/{company}/jobs`
- ✅ **Status**: Tested and working with Anthropic

### 4. **Factory Function** (`app/extractors/factory.py`)
- ✅ Created `list_company_engineering_jobs()` function
- ✅ Routes to appropriate extractor based on URL
- ✅ Filters for engineering roles
- ✅ Limits results to 20 jobs
- ✅ Converts to Pydantic models for API response
- ✅ Registered all new extractors

### 5. **API Endpoint** (`app/api/endpoints.py`)
- ✅ Added POST `/company-engineering-jobs` endpoint
- ✅ Accepts JobUrlRequest (URL)
- ✅ Returns CompanyJobsResponse (company, total_jobs, engineering_jobs)
- ✅ Comprehensive documentation in docstring

### 6. **Schemas** (`app/schemas/job.py`)
- ✅ Already had `JobListing` model
- ✅ Already had `CompanyJobsResponse` model
- ✅ No changes needed

### 7. **Test Scripts**

#### `scripts/test_company_jobs.py`
- ✅ Tests extractors directly
- ✅ Tests Ashby and Greenhouse URLs
- ✅ Can be extended for other platforms

#### `scripts/test_api_endpoint.py`
- ✅ Tests the API endpoint via HTTP
- ✅ Tests Ashby and Greenhouse URLs
- ✅ Requires server to be running

#### Debug Scripts (for development)
- `scripts/debug_ashby.py`
- `scripts/inspect_ashby.py`
- `scripts/find_ashby_api.py`
- `scripts/find_greenhouse_api.py`

## Test Results

### ✅ Ashby (St Labs)
```
Company: St Labs
Found 10 engineering jobs
- Senior Software Engineer
- Full Stack Software Engineer
- Staff Software Engineer
- Principal Software Engineer
- Senior Platform Engineer
- AI Engineer
- IT Operations & Trust Engineer
- Senior Software Engineer - Graph Database
- Front-End Engineer
- Sr. Front-End Engineer
```

### ✅ Greenhouse (Anthropic)
```
Company: Anthropic
Found 20 engineering jobs (limited from 365 total)
- Analytics Data Engineer
- Application Security Engineer
- Application Security Engineering Manager
- Applied AI Engineer, Beneficial Deployments
- Applied AI Engineer (Digital Natives Business)
- ... and 15 more
```

## Files Created

```
app/utils/__init__.py
app/utils/filters.py
app/extractors/lever.py
app/extractors/workday.py
app/extractors/rippling.py
scripts/test_company_jobs.py
scripts/test_api_endpoint.py
scripts/debug_ashby.py
scripts/inspect_ashby.py
scripts/find_ashby_api.py
scripts/find_greenhouse_api.py
COMPANY_JOBS_ENDPOINT.md
IMPLEMENTATION_SUMMARY.md
```

## Files Modified

```
app/extractors/base.py (unchanged - already had the methods)
app/extractors/ashby.py (added company job listing methods)
app/extractors/greenhouse.py (added company job listing methods)
app/extractors/factory.py (added new function and registered extractors)
app/schemas/job.py (unchanged - already had required schemas)
app/api/endpoints.py (added new endpoint)
```

## How to Use

### Start the server
```bash
uvicorn app.main:app --reload
```

### Test with cURL
```bash
# Ashby
curl -X POST http://localhost:8000/company-engineering-jobs \
  -H "Content-Type: application/json" \
  -d '{"url": "https://jobs.ashbyhq.com/st-labs/8cc33e27-fe89-41b8-95e4-9f47540ea8d4"}'

# Greenhouse
curl -X POST http://localhost:8000/company-engineering-jobs \
  -H "Content-Type: application/json" \
  -d '{"url": "https://job-boards.greenhouse.io/anthropic/jobs/5077227008"}'
```

### Test with Python
```bash
python scripts/test_company_jobs.py
python scripts/test_api_endpoint.py
```

## Next Steps / TODO

1. **Test Untested Platforms**
   - Find test URLs for Lever
   - Find test URLs for Workday
   - Find test URLs for Rippling
   - Verify and adjust extractors as needed

2. **Improvements**
   - Add caching for API responses
   - Implement rate limiting
   - Add pagination support
   - Allow customizable job limits
   - Better error messages

3. **Documentation**
   - Update main README.md
   - Add API documentation
   - Add deployment guide

## Notes

- Ashby and Greenhouse use JavaScript SPAs, so we had to use their APIs instead of HTML scraping
- Lever and Rippling also have public APIs which should work
- Workday is the most challenging as it has no public API and varies significantly by company
- The filtering keywords can be adjusted in `app/utils/filters.py` if needed
- All extractors handle errors gracefully and return empty lists on failure
