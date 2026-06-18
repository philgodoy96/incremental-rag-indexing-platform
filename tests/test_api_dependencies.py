from unittest.mock import patch

from app.api.dependencies import get_llm_provider
from app.config.settings import Settings
from app.providers.fake_llm_provider import FakeLLMProvider


def test_get_llm_provider_returns_fake_by_default() -> None:
    fake_settings = Settings(llm_provider="fake")

    with patch("app.api.dependencies.get_settings", return_value=fake_settings):
        provider = get_llm_provider()

    assert isinstance(provider, FakeLLMProvider)
