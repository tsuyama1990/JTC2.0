import httpx
from langchain_openai import ChatOpenAI

from src.core.config import get_settings
from src.core.constants import ERR_LLM_CONFIG_MISSING

_llm_cache: dict[str, ChatOpenAI] = {}
_cached_key_hash: str | None = None

def _hash_key(key: str) -> str:
    import hashlib
    return hashlib.sha256(key.encode()).hexdigest()

def get_llm(model: str | None = None) -> ChatOpenAI:
    """
    Factory to get the LLM client with built-in connection pooling and retries.
    Uses custom caching mechanism based on model name and secure key hash to support rotation.
    """
    global _llm_cache, _cached_key_hash
    settings = get_settings()
    if not settings.openai_api_key:
        raise ValueError(ERR_LLM_CONFIG_MISSING)

    current_key = settings.openai_api_key.get_secret_value()
    current_hash = _hash_key(current_key)

    if _cached_key_hash != current_hash:
        _llm_cache.clear()
        _cached_key_hash = current_hash

    target_model = model or settings.llm_model
    if target_model in _llm_cache:
        return _llm_cache[target_model]

    # Use httpx.Client with explicit limits to prevent connection leaking
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
    timeout = httpx.Timeout(60.0, connect=10.0)
    http_client = httpx.Client(limits=limits, timeout=timeout)

    client = ChatOpenAI(
        model=target_model,
        api_key=settings.openai_api_key,
        max_retries=settings.resiliency.circuit_breaker_fail_max,
        http_client=http_client
    )
    _llm_cache[target_model] = client
    return client

def clear_llm_cache() -> None:
    """Clear the LLM client cache to release resources or rotate keys."""
    global _llm_cache, _cached_key_hash
    _llm_cache.clear()
    _cached_key_hash = None
