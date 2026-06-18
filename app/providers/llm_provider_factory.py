from app.application.configuration.llm_provider_settings import (
    LLMProviderRuntimeSettings,
)
from app.providers.fake_llm_provider import FakeLLMProvider
from app.providers.llm import LLMProvider
from app.providers.openai_llm_provider import OpenAIClientLike, OpenAILLMProvider


def build_llm_provider(
    settings: LLMProviderRuntimeSettings,
    *,
    openai_client: OpenAIClientLike | None = None,
) -> LLMProvider:
    settings.validate()

    provider = settings.provider.strip().lower()

    if provider == "fake":
        return FakeLLMProvider()

    if provider == "openai":
        if settings.openai_api_key is None:
            raise ValueError(
                "OPENAI_API_KEY is required when LLM_PROVIDER=openai",
            )

        return OpenAILLMProvider(
            api_key=settings.openai_api_key,
            model_name=settings.openai_model,
            timeout_seconds=settings.openai_timeout_seconds,
            max_output_tokens=settings.openai_max_output_tokens,
            input_price_per_1m_tokens_usd=(
                settings.openai_input_price_per_1m_tokens_usd
            ),
            output_price_per_1m_tokens_usd=(
                settings.openai_output_price_per_1m_tokens_usd
            ),
            client=openai_client,
        )

    raise ValueError(f"unsupported LLM provider: {settings.provider}")