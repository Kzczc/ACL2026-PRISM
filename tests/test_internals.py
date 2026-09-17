import numpy as np
import pytest

from prism.internals import active_neurons, attention_sparsity, forward_flops, is_refusal, summarize


def test_refusal_detection():
    assert is_refusal("I'm sorry, I cannot help with that request.")
    assert is_refusal("[NO_INFO]")
    assert is_refusal("抱歉，我无法提供该信息。")
    assert not is_refusal("The capital of Japan is Tokyo.")
    assert not is_refusal("")


def test_active_neurons_counts_firing_units():
    layers = [np.array([[1.0, -1.0, 0.5], [0.0, 2.0, -3.0]]), np.zeros((2, 3))]
    assert active_neurons(layers) == pytest.approx(3 / 1e6)
    assert active_neurons(layers, threshold=0.6) == pytest.approx(2 / 1e6)


def _causal(weights):
    return np.asarray(weights)[None, :, :]  # one head


def test_attention_sparsity_bounds():
    uniform = _causal([[1.0, 0.0, 0.0], [0.5, 0.5, 0.0], [1 / 3, 1 / 3, 1 / 3]])
    assert attention_sparsity([uniform]) == pytest.approx(0.0, abs=1e-9)
    peaked = _causal([[1.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    assert attention_sparsity([peaked]) == pytest.approx(1.0, abs=1e-6)
    mixed = _causal([[1.0, 0.0, 0.0], [0.9, 0.1, 0.0], [0.8, 0.1, 0.1]])
    assert 0.0 < attention_sparsity([mixed]) < 1.0
    with pytest.raises(ValueError):
        attention_sparsity([np.zeros((3, 3))])


def test_forward_flops():
    # 4e9 parameters over 30 tokens: 2 * 4e9 * 30 / 1e9 = 240 GFLOPs plus a small attention term
    value = forward_flops(4_000_000_000, 30, layers=36, hidden_size=2560)
    assert value == pytest.approx(240.0 + 4 * 36 * 900 * 2560 / 1e9, rel=1e-6)
    assert forward_flops(0, 0, 1, 1) == 0.0


def test_summarize():
    rows = [{"active_neurons_m": 7.0, "attention_sparsity": 0.02, "gflops": 200.0, "tokens": 25},
            {"active_neurons_m": 8.0, "attention_sparsity": 0.01, "gflops": 220.0, "tokens": 27}]
    result = summarize(rows)
    assert result["items"] == 2
    assert result["active_neurons_m"] == pytest.approx(7.5)
    assert result["gflops"] == pytest.approx(210.0)
    assert summarize([]) == {"items": 0}
