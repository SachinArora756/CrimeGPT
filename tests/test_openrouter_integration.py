"""Quick integration test for OpenRouter fallback functionality.

Requires OPENROUTER_API_KEY in environment or ../.env file.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")


def _setup_env():
    os.environ["OPENROUTER_API_KEY"] = API_KEY
    os.environ["GEMINI_API_KEY"] = ""
    from importlib import reload
    import app.config
    reload(app.config)
    import app.ai.llm_provider as provider
    reload(provider)
    return provider


def test_config_loads_openrouter_key():
    """Verify the config picks up the OPENROUTER_API_KEY env var."""
    from app.config import Settings
    s = Settings(openrouter_api_key="sk-or-v1-testkey1234567890")
    assert s.openrouter_api_key == "sk-or-v1-testkey1234567890"
    print("[PASS] Config loads openrouter_api_key")


def test_has_any_llm_key():
    """Verify has_any_llm_key detects OpenRouter key."""
    provider = _setup_env()
    assert provider.has_any_llm_key() is True
    assert provider._has_openrouter_key() is True
    assert provider._has_gemini_key() is False
    print("[PASS] has_any_llm_key detects OpenRouter")


def test_get_llm_returns_chatopenai():
    """Verify get_llm() returns a ChatOpenAI instance when only OpenRouter is set."""
    provider = _setup_env()
    llm = provider.get_llm()
    assert "ChatOpenAI" in type(llm).__name__
    print("[PASS] get_llm() returns ChatOpenAI for OpenRouter")


def test_generate_text_works():
    """Test actual API call to OpenRouter."""
    provider = _setup_env()
    result = provider.generate_text("Reply with exactly: HELLO_CRIMEGPT", temperature=0.0, max_tokens=20)
    assert "HELLO" in result.upper() or "CRIMEGPT" in result.upper()
    print(f"[PASS] generate_text works. Response: {result.strip()[:80]}")


def test_get_llm_invoke():
    """Test LangChain LLM invoke via OpenRouter."""
    provider = _setup_env()
    llm = provider.get_llm(temperature=0.0)
    response = llm.invoke("Reply with exactly one word: WORKING")
    assert response.content
    print(f"[PASS] LangChain LLM invoke works. Response: {response.content.strip()[:80]}")


if __name__ == "__main__":
    print("=" * 60)
    print("CrimeGPT OpenRouter Integration Tests")
    print("=" * 60)

    if not API_KEY or len(API_KEY) < 10:
        print("[SKIP] OPENROUTER_API_KEY not found in environment or .env file")
        print("Set it to run live API tests.")
        sys.exit(0)

    tests = [
        test_config_loads_openrouter_key,
        test_has_any_llm_key,
        test_get_llm_returns_chatopenai,
        test_generate_text_works,
        test_get_llm_invoke,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test.__name__}: {e}")
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 60)
    sys.exit(0 if failed == 0 else 1)
