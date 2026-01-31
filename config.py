from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    llm_provider: str = "local"

    # Local LLM (OpenAI-compatible server)
    local_llm_base_url: str = "http://localhost:11434/v1"
    local_llm_model: str = "llama3"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    model_config = {"env_file": ".env"}


settings = Settings()
