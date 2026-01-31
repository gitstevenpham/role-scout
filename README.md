# Role Scout

A FastAPI service that extracts and summarizes job listings from various Applicant Tracking Systems (ATS).

## Features

- 🔍 **Job Extraction**: Automatically extracts job descriptions from URLs
- 🤖 **AI Summarization**: Uses LLM to generate structured summaries
- 🎯 **Multi-ATS Support**: Works with Ashby, Greenhouse, and LinkedIn
- ⚡ **Fast API**: RESTful API built with FastAPI

## Supported Platforms

- **Ashby** (`ashbyhq.com`)
- **Greenhouse** (`greenhouse.io`, `boards.greenhouse.io`)
- **LinkedIn** (`linkedin.com/jobs`)

## Project Structure

```
role-scout/
├── app/                    # Main application package
│   ├── api/               # API endpoints
│   ├── extractors/        # Job extraction logic
│   ├── schemas/           # Pydantic models
│   ├── services/          # Business logic
│   ├── config.py          # Configuration
│   └── main.py            # FastAPI app
├── tests/                 # Test suite
├── scripts/               # Utility scripts
└── requirements.txt       # Dependencies
```

## Installation

1. Clone the repository:
```bash
git clone <repo-url>
cd role-scout
```

2. Create virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your settings
```

## Usage

### Start the API Server

```bash
python app/main.py
```

Or with uvicorn:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation

Interactive API docs: `http://localhost:8000/docs`

### Endpoints

**Health Check**
```bash
GET /
```

**Summarize Job**
```bash
POST /summarize-job
Content-Type: application/json

{
  "url": "https://jobs.ashbyhq.com/company/job-id"
}
```

**Response:**
```json
{
  "url": "https://jobs.ashbyhq.com/company/job-id",
  "summary": "Job Title: Senior Software Engineer\n..."
}
```

### Test Extractors

Run the test script to verify extractors work:

```bash
python scripts/run_extractors.py
```

### Run Tests

```bash
pytest tests/ -v
```

## Configuration

Configure via `.env` file or environment variables:

- `LLM_PROVIDER`: `local` or `openai`
- `OPENAI_API_KEY`: Your OpenAI API key (if using OpenAI)
- `OPENAI_MODEL`: Model to use (e.g., `gpt-4`)
- `LOCAL_LLM_BASE_URL`: Base URL for local LLM (e.g., LM Studio)
- `LOCAL_LLM_MODEL`: Local model name

## Adding New ATS Platforms

1. Create a new extractor in `app/extractors/` (e.g., `lever.py`)
2. Inherit from `BaseJobExtractor`
3. Implement `can_handle()` and `extract()` methods
4. Add to `EXTRACTORS` list in `factory.py`

Example:
```python
from .base import BaseJobExtractor

class LeverExtractor(BaseJobExtractor):
    @staticmethod
    def can_handle(url: str) -> bool:
        return "lever.co" in url

    def extract(self, url: str) -> Optional[str]:
        # Implementation
        pass
```

## Development

### Code Style

Format code with Black:
```bash
black app/ tests/
```

### Linting

```bash
ruff check app/ tests/
```

## License

MIT

## Contributing

Pull requests are welcome! Please ensure tests pass before submitting.
