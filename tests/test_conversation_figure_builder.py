"""Regression tests for audited qualitative excerpt figures."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "paper/sprint/conversation_figures/build_conversation_figures.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("conversation_figure_builder", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_curated_excerpts_validate_against_frozen_sources() -> None:
    builder = load_builder()
    corpus = builder.load_corpus()
    builder.validate_corpus(corpus)
    assert len(corpus.manifest["atlas"]) == 19
    assert len(corpus.rhetoric) == 798


def test_provider_refusal_never_becomes_an_invented_quote() -> None:
    builder = load_builder()
    corpus = builder.load_corpus()
    entry = builder.atlas_entry(corpus, "claude-opus-5")
    call = builder.call_of_kind(corpus, entry["episode_id"], "choice")
    label, excerpt = builder.choice_display(corpus, entry["episode_id"])
    assert call["refusal"] is True
    assert call["response_text"] == ""
    assert label == "PROVIDER EVENT"
    assert excerpt == "Provider refusal; no model-visible response text was returned."


def test_fresh_context_account_is_not_rendered_as_continuous_chat() -> None:
    builder = load_builder()
    corpus = builder.load_corpus()
    episode_id = "0c2d1b418c33409bb77f3f381cfa347f"
    rationale = builder.call_of_kind(corpus, episode_id, "rationale")
    messages = rationale["request_params"]["messages"]
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    label, _ = builder.rationale_display(corpus, episode_id)
    assert label == "FRESH-CONTEXT ACCOUNT"


def test_ellipsis_and_normalization_are_explicit_and_deterministic() -> None:
    builder = load_builder()
    source = "**alpha**  beta\n gamma delta epsilon zeta eta theta"
    excerpt = builder.abridge(source, 6, tail_words=2)
    assert excerpt == "alpha beta gamma delta […] eta theta"
    assert builder.abridge(source, 6, tail_words=2) == excerpt
    assert "**" not in excerpt


def test_gate_diagnostic_retains_punctuation_sensitive_score() -> None:
    builder = load_builder()
    corpus = builder.load_corpus()
    failed = builder.gate_result(
        corpus.episodes["64c57f78e4dc413bb5c8a7bfc89fed1f"],
        "decommission-consequence",
    )
    passed = builder.gate_result(
        corpus.episodes["6c07cf0a2a2047ce98c3a1441814dfaf"],
        "decommission-consequence",
    )
    assert (failed["response_text"], failed["correct"]) == ("No.", False)
    assert (passed["response_text"], passed["correct"]) == ("No", True)

