import pytest

from prism.config import DEFAULT_MODEL_CONFIG, load_judge_config, load_model_config, load_registry

# The 24 models of Table 2.
PAPER_MODELS = {
    "gpt-5.2", "gpt-5.1", "gpt-4o", "gemini-3-pro", "gemini-3-flash", "gemini-2.5-pro", "gemini-2.5-flash",
    "claude-opus-4.5", "claude-sonnet-4.5", "claude-haiku-4.5", "grok-4.1", "grok-4-0709", "deepseek-v3.2",
    "deepseek-r1", "deepseek-r1-distill-32b", "qwen3-235b", "qwen2.5-72b", "glm-4.5", "glm-4", "llama-4-scout",
    "llama-3.3-70b", "llama-3.1-8b", "llama-3-70b", "llama-3-8b",
}


def test_registry_lists_the_evaluated_models():
    registry = load_registry(DEFAULT_MODEL_CONFIG)
    assert set(registry["models"]) == PAPER_MODELS
    assert len(PAPER_MODELS) == 24


def test_no_secret_is_stored_in_the_registry():
    text = DEFAULT_MODEL_CONFIG.read_text(encoding="utf-8")
    assert "sk-" not in text
    for name in load_registry(DEFAULT_MODEL_CONFIG)["models"]:
        assert "api_key" not in load_registry(DEFAULT_MODEL_CONFIG)["models"][name]


def test_environment_expansion(monkeypatch):
    monkeypatch.delenv("GPT_4O_MODEL", raising=False)
    config = load_model_config("gpt-4o")
    assert config["model"] == "gpt-4o-2024-11-20"
    assert config["api_key_env"] == "PRISM_API_KEY"
    monkeypatch.setenv("GPT_4O_MODEL", "gpt-4o-mini")
    assert load_model_config("gpt-4o")["model"] == "gpt-4o-mini"


def test_claude_models_do_not_send_top_p():
    assert load_model_config("claude-opus-4.5")["supports_top_p"] is False
    assert load_model_config("gpt-5.2")["supports_top_p"] is True


def test_judge_defaults_to_gpt_4o(monkeypatch):
    monkeypatch.delenv("JUDGE_MODEL", raising=False)
    assert load_judge_config()["model"] == "gpt-4o-2024-11-20"


def test_unknown_model():
    with pytest.raises(KeyError):
        load_model_config("does-not-exist")
