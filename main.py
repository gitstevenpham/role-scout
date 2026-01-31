from fastapi import FastAPI
from openai import AsyncOpenAI

from config import settings

app = FastAPI(title="LLM Chat Service")


def get_llm_client() -> tuple[AsyncOpenAI, str]:
    if settings.llm_provider == "openai":
        return AsyncOpenAI(api_key=settings.openai_api_key), settings.openai_model
    return (
        AsyncOpenAI(base_url=settings.local_llm_base_url, api_key="not-needed"),
        settings.local_llm_model,
    )


@app.get("/")
async def health():
    return {"status": "ok", "provider": settings.llm_provider}


@app.post("/chat")
async def chat(message: str = "hello world"):
    client, model = get_llm_client()
    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": message}],
    )
    return {
        "provider": settings.llm_provider,
        "model": model,
        "message": message,
        "reply": response.choices[0].message.content,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
