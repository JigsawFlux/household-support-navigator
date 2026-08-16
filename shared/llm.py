# shared/llm.py
import os


def get_llm(temperature: float = 0.0):
    """
    LLM factory. Reads LLM_PROVIDER env var and returns the appropriate
    LangChain chat model instance.

    Supported providers:
      - "anthropic" (default) -> ChatAnthropic, uses CLAUDE_MODEL
      - "ollama"               -> ChatOllama, uses OLLAMA_MODEL

    All tool modules must call get_llm() instead of importing a
    provider-specific chat model directly, so the provider can be swapped
    via environment variable without code changes.
    """
    provider = os.environ.get("LLM_PROVIDER", "anthropic").strip().lower()

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        model = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        return ChatOllama(model=model, base_url=base_url, temperature=temperature)

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic"
            )
        model = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")
        return ChatAnthropic(model=model, temperature=temperature, api_key=api_key)

    raise ValueError(
        f"Unsupported LLM_PROVIDER '{provider}'. Use 'anthropic' or 'ollama'."
    )