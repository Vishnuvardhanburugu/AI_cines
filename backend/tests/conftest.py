import os

import pytest

# Force mock provider for unit/integration tests unless LIVE_EVAL=1
os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("IMAGE_PROVIDER", "mock")
os.environ.setdefault("OPENAI_API_KEY", "")
os.environ.setdefault("GEMINI_API_KEY", "")


@pytest.fixture
def mock_provider():
    from app.providers.mock import MockProvider

    return MockProvider()
