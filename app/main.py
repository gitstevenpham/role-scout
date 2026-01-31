"""FastAPI application entry point."""

from fastapi import FastAPI
from app.api.endpoints import router

app = FastAPI(
    title="Role Scout",
    description="Job listing extraction and summarization service",
    version="0.1.0",
)

# Include API routes
app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
