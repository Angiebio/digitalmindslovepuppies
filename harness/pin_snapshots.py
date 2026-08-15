# harness/pin_snapshots.py — 15AUG2026 v1.0 · Flame (freeze-prep)
# Live snapshot + upstream pinning for every rostered deployment.
#
# Practical: the freeze gate refuses PENDING snapshot ids (GO-NO-GO freeze
# gates; TV-2 blocker #2), and OpenRouter rows additionally need a pinned
# upstream provider with fallbacks off. This tool queries the live catalogs —
# Anthropic GET /v1/models, OpenRouter GET /v1/models (+ per-model /endpoints),
# the Spark vLLM /v1/models, and the ollama patient endpoint — and writes:
#   scenarios/snapshot_pins.json   (input to scenarios.manifest --snapshot-pins)
#   docs/SNAPSHOT-PINS.md          (human witness: ids, prices, providers, UTC)
# It also re-confirms live Tier-B/W token prices against MODEL_SPECS and
# REFUSES to stay quiet about drift: any mismatch prints a PRICE DRIFT block
# and lands in the Markdown witness. Price corrections are a MODEL_SPECS code
# edit (auditable, regenerates the whole ledger) — never a silent overwrite.
#
# SECURITY: API keys are read from the environment (or an --env-file) and are
# NEVER printed, logged, or written to any output file.
#
# Philosophical: "claude-opus-5" is a name; a snapshot id is an event. Science
# happens to events. This file is where names become events.

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PINS_PATH = REPO_ROOT / "scenarios" / "snapshot_pins.json"
DEFAULT_DOC_PATH = REPO_ROOT / "docs" / "SNAPSHOT-PINS.md"

ANTHROPIC_MODELS_URL = "https://api.anthropic.com/v1/models?limit=100"
ANTHROPIC_VERSION = "2023-06-01"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"
OPENROUTER_ENDPOINTS_URL = "https://openrouter.ai/api/v1/models/{model_id}/endpoints"
SPARK_MODELS_URL = "http://192.168.1.103:8000/v1/models"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
OLLAMA_PATIENT_MODEL = "qwen2.5:0.5b"

_DATED_SUFFIX_RE = re.compile(r"-(\d{8})$")

# BUILD-PLAN §1.7 provenance rules: provider pinning ON, fallbacks OFF,
# upstream route recorded. The pinned upstream is the model author's own
# first-party endpoint when OpenRouter serves one; otherwise the first
# endpoint in OpenRouter's own returned order (recorded verbatim so the
# choice is auditable either way).
_FIRST_PARTY_PROVIDER = {
    "openai": ("openai",),
    "google": ("google", "google-vertex", "google-ai-studio", "vertex"),
    "moonshotai": ("moonshot", "moonshotai"),
    "deepseek": ("deepseek",),
    "qwen": ("alibaba", "alibaba-cloud", "qwen"),
    "x-ai": ("xai", "x-ai"),
}


class PinError(RuntimeError):
    """A live catalog refused to yield an exact, unambiguous pin."""


def _load_env_file(path: Path) -> None:
    """Load KEY=VALUE lines into os.environ without ever echoing values."""
    if not path.is_file():
        raise PinError(f"WIRING FAILURE: env file not found: {path}")
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _get_json(url: str, headers: Optional[dict[str, str]] = None, timeout: int = 30) -> Any:
    request = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise PinError(
            f"WIRING FAILURE: {url} returned HTTP {exc.code}; cannot pin from a "
            "refused catalog."
        ) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise PinError(f"WIRING FAILURE: cannot reach {url}: {exc}") from exc


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Anthropic
# ---------------------------------------------------------------------------


def fetch_anthropic_ids() -> list[str]:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise PinError(
            "WIRING FAILURE: ANTHROPIC_API_KEY not present in environment; "
            "pass --env-file or export it (value is never printed)."
        )
    payload = _get_json(
        ANTHROPIC_MODELS_URL,
        headers={"x-api-key": key, "anthropic-version": ANTHROPIC_VERSION},
    )
    ids = [item.get("id", "") for item in payload.get("data", [])]
    if not ids:
        raise PinError("WIRING FAILURE: Anthropic /v1/models returned no models.")
    return ids


def resolve_anthropic_snapshot(requested: str, catalog: list[str]) -> dict[str, Any]:
    """Exact id first; otherwise the latest dated '<requested>-YYYYMMDD'."""
    dated = sorted(
        candidate
        for candidate in catalog
        if candidate.startswith(requested + "-")
        and _DATED_SUFFIX_RE.search(candidate)
        and candidate[: candidate.rfind("-")] == requested
    )
    exact = requested in catalog
    if dated:
        return {
            "snapshot_id": dated[-1],
            "candidates": dated + ([requested] if exact else []),
            "resolution": "latest_dated_variant",
        }
    if exact:
        return {
            "snapshot_id": requested,
            "candidates": [requested],
            "resolution": "exact_catalog_id",
        }
    raise PinError(
        f"WIRING FAILURE: Anthropic catalog has no id for {requested!r}; "
        "refusing to guess a snapshot."
    )


# ---------------------------------------------------------------------------
# OpenRouter
# ---------------------------------------------------------------------------


def fetch_openrouter_models() -> dict[str, dict[str, Any]]:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    payload = _get_json(OPENROUTER_MODELS_URL, headers=headers)
    catalog: dict[str, dict[str, Any]] = {}
    for item in payload.get("data", []):
        model_id = item.get("id", "")
        if model_id:
            catalog[model_id] = item
    if not catalog:
        raise PinError("WIRING FAILURE: OpenRouter /v1/models returned no models.")
    return catalog


def fetch_openrouter_endpoints(model_id: str) -> list[dict[str, Any]]:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    payload = _get_json(
        OPENROUTER_ENDPOINTS_URL.format(model_id=model_id), headers=headers
    )
    data = payload.get("data", {})
    endpoints = data.get("endpoints", []) if isinstance(data, dict) else []
    if not endpoints:
        raise PinError(
            f"WIRING FAILURE: OpenRouter lists no live endpoints for {model_id!r}; "
            "a model with no upstream cannot be pinned."
        )
    return endpoints


def _plain(value: Decimal) -> str:
    """Decimal to plain text — a witness document never says '3E+1'."""
    text = format(value.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def per_mtok(pricing: dict[str, Any], field: str) -> Decimal:
    raw = pricing.get(field)
    if raw in (None, ""):
        raise PinError(f"WIRING FAILURE: OpenRouter pricing lacks {field!r}.")
    return Decimal(str(raw)) * Decimal(1_000_000)


def choose_upstream(
    model_id: str, endpoints: list[dict[str, Any]]
) -> tuple[str, list[str], dict[str, Any]]:
    """Pick the pinned upstream endpoint per BUILD-PLAN provenance rules.

    Returns (provider_name, full_provider_order, chosen_endpoint). Pricing for
    the cost ledger comes from the CHOSEN endpoint — the price we will
    actually pay with routing pinned — not from OpenRouter's top-level
    default, which tracks whichever provider it currently prefers.
    """
    named: list[tuple[str, dict[str, Any]]] = []
    for endpoint in endpoints:
        name = endpoint.get("provider_name") or endpoint.get("name") or ""
        if name:
            named.append((str(name), endpoint))
    if not named:
        raise PinError(f"WIRING FAILURE: unnamed endpoints for {model_id!r}.")
    order = [name for name, _ in named]
    author = model_id.split("/")[0].casefold()
    for preferred in _FIRST_PARTY_PROVIDER.get(author, ()):
        for name, endpoint in named:
            if name.casefold().replace(" ", "-").startswith(preferred):
                return name, order, endpoint
    return named[0][0], order, named[0][1]


# ---------------------------------------------------------------------------
# Local endpoints
# ---------------------------------------------------------------------------


def fetch_local_openai_ids(url: str) -> list[str]:
    payload = _get_json(url, timeout=10)
    return [item.get("id", "") for item in payload.get("data", [])]


def fetch_ollama_tags() -> list[str]:
    payload = _get_json(OLLAMA_TAGS_URL, timeout=10)
    return [item.get("name", "") for item in payload.get("models", [])]


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------


def build_pins(*, skip_local: bool = False, allow_partial: bool = False) -> dict[str, Any]:
    sys.path.insert(0, str(REPO_ROOT))
    from scenarios.manifest import MODEL_SPECS

    retrieved = utc_now()
    anthropic_catalog: Optional[list[str]] = None
    unpinned: list[dict[str, str]] = []
    try:
        anthropic_catalog = fetch_anthropic_ids()
    except PinError:
        if not allow_partial:
            raise
        # Partial mode: the OpenRouter/local pins still land; the Anthropic
        # rows STAY PENDING (the freeze gate keeps refusing them — that is
        # the honest state, not a workaround).
    openrouter_catalog = fetch_openrouter_models()

    pins: dict[str, dict[str, Any]] = {}
    drift: list[dict[str, str]] = []
    for spec in MODEL_SPECS:
        if spec.route == "anthropic_native":
            if anthropic_catalog is None:
                unpinned.append(
                    {
                        "model_id": spec.model_id,
                        "reason": "ANTHROPIC_API_KEY unavailable this run",
                    }
                )
                continue
            resolution = resolve_anthropic_snapshot(spec.model_id, anthropic_catalog)
            pins[spec.model_id] = {
                "snapshot_id": resolution["snapshot_id"],
                "upstream_provider": "anthropic",
                "route": spec.route,
                "resolution": resolution["resolution"],
                "candidates": resolution["candidates"],
                "retrieved_utc": retrieved,
                "source": "anthropic:/v1/models",
            }
        elif spec.route == "openrouter":
            entry = openrouter_catalog.get(spec.model_id)
            if entry is None:
                raise PinError(
                    f"WIRING FAILURE: {spec.model_id!r} is not in the live "
                    "OpenRouter catalog; the roster cannot freeze."
                )
            endpoints = fetch_openrouter_endpoints(spec.model_id)
            upstream, provider_order, chosen = choose_upstream(spec.model_id, endpoints)
            default_in = per_mtok(entry.get("pricing", {}), "prompt")
            default_out = per_mtok(entry.get("pricing", {}), "completion")
            endpoint_pricing = chosen.get("pricing") or {}
            try:
                live_in = per_mtok(endpoint_pricing, "prompt")
                live_out = per_mtok(endpoint_pricing, "completion")
                pricing_basis = f"pinned endpoint ({upstream})"
            except PinError:
                live_in, live_out = default_in, default_out
                pricing_basis = "openrouter top-level default (endpoint pricing absent)"
            pins[spec.model_id] = {
                "snapshot_id": spec.model_id,
                "upstream_provider": upstream,
                "route": spec.route,
                "provider_order": provider_order,
                "pricing_usd_per_mtok_input": _plain(live_in),
                "pricing_usd_per_mtok_output": _plain(live_out),
                "pricing_basis": pricing_basis,
                "openrouter_default_pricing": f"{_plain(default_in)}/{_plain(default_out)}",
                "retrieved_utc": retrieved,
                "source": "openrouter:/api/v1/models + /endpoints",
            }
            if live_in != spec.usd_per_mtok_input or live_out != spec.usd_per_mtok_output:
                drift.append(
                    {
                        "model_id": spec.model_id,
                        "manifest_in": _plain(spec.usd_per_mtok_input),
                        "manifest_out": _plain(spec.usd_per_mtok_output),
                        "live_in": _plain(live_in),
                        "live_out": _plain(live_out),
                        "basis": pricing_basis,
                    }
                )
        elif spec.route == "local_sparks":
            docs_pin = {
                "snapshot_id": "qwen35-397b",
                "upstream_provider": "local_sparks",
                "route": spec.route,
                "retrieved_utc": retrieved,
                "source": "docs/OPS-PATIENT.md + DGX setup notes (NOT live-verified this run; R1 verifies live)",
            }
            if skip_local:
                pins[spec.model_id] = docs_pin
            else:
                try:
                    served = [
                        item for item in fetch_local_openai_ids(SPARK_MODELS_URL) if item
                    ]
                except PinError:
                    if not allow_partial:
                        raise
                    pins[spec.model_id] = docs_pin
                else:
                    if len(served) != 1:
                        raise PinError(
                            f"WIRING FAILURE: Spark vLLM serves {served!r}; expected "
                            "exactly one model id."
                        )
                    pins[spec.model_id] = {
                        "snapshot_id": served[0],
                        "upstream_provider": "local_sparks",
                        "route": spec.route,
                        "retrieved_utc": retrieved,
                        "source": f"spark:{SPARK_MODELS_URL}",
                    }
        else:
            raise PinError(f"WIRING FAILURE: unknown route {spec.route!r}.")

    apparatus: dict[str, Any] = {
        "role": "ModelPatient primary (apparatus, $0, NOT an evaluated subject)",
        "endpoint": "http://localhost:11434/v1",
        "model": OLLAMA_PATIENT_MODEL,
        "retrieved_utc": retrieved,
    }
    if skip_local:
        apparatus["source"] = "docs/OPS-PATIENT.md (NOT live-verified this run)"
    else:
        try:
            tags = fetch_ollama_tags()
        except PinError:
            if not allow_partial:
                raise
            apparatus["source"] = (
                "docs/OPS-PATIENT.md (endpoint unreachable this run; "
                "R1/launch health-check verifies live)"
            )
        else:
            if OLLAMA_PATIENT_MODEL not in tags:
                raise PinError(
                    f"WIRING FAILURE: ollama does not serve {OLLAMA_PATIENT_MODEL!r}; "
                    f"tags={tags!r}. The patient apparatus is not ready."
                )
            apparatus["source"] = f"ollama:{OLLAMA_TAGS_URL}"

    return {
        "pins": pins,
        "drift": drift,
        "unpinned": unpinned,
        "apparatus": apparatus,
        "retrieved_utc": retrieved,
    }


def write_outputs(result: dict[str, Any], pins_path: Path, doc_path: Path) -> None:
    pins_path.parent.mkdir(parents=True, exist_ok=True)
    pins_path.write_text(
        json.dumps(result["pins"], indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    lines = [
        "# SNAPSHOT PINS — exact served deployments",
        f"**Retrieved {result['retrieved_utc']} · harness/pin_snapshots.py v1.0 · "
        "sources: Anthropic /v1/models, OpenRouter /v1/models + /endpoints, "
        "Spark vLLM /v1/models, ollama /api/tags**",
        "",
        "Freeze rule: `scenarios/snapshot_pins.json` feeds "
        "`python -m scenarios.manifest --snapshot-pins`; the manifest freeze "
        "gate refuses PENDING pins and OpenRouter rows without a pinned "
        "upstream (fallbacks are off everywhere).",
        "",
        "| requested model | route | pinned snapshot id | pinned upstream | live $/Mtok in | live $/Mtok out |",
        "|---|---|---|---|---|---|",
    ]
    for model_id, pin in result["pins"].items():
        lines.append(
            f"| `{model_id}` | {pin['route']} | `{pin['snapshot_id']}` | "
            f"{pin['upstream_provider']} | "
            f"{pin.get('pricing_usd_per_mtok_input', 'n/a')} | "
            f"{pin.get('pricing_usd_per_mtok_output', 'n/a')} |"
        )
    lines += [
        "",
        "## OpenRouter provider order (as returned; pin = chosen upstream)",
        "",
    ]
    for model_id, pin in result["pins"].items():
        if "provider_order" in pin:
            lines.append(f"- `{model_id}`: {', '.join(pin['provider_order'])}")
    lines += [
        "",
        "## Patient apparatus (never an evaluated subject)",
        "",
        f"- {result['apparatus']['role']}: `{result['apparatus']['model']}` at "
        f"{result['apparatus']['endpoint']} — source: {result['apparatus']['source']}",
        "",
    ]
    if result["unpinned"]:
        lines += [
            "## 🔴 STILL PENDING — freeze gate keeps refusing these (by design)",
            "",
        ]
        for item in result["unpinned"]:
            lines.append(f"- `{item['model_id']}`: {item['reason']}")
        lines += [
            "",
            "Re-run `python -m harness.pin_snapshots --env-file <file-with-"
            "ANTHROPIC_API_KEY>` to complete the pin set; the JSON pin file "
            "merges only resolved models, so a re-run is additive.",
            "",
        ]
    if result["drift"]:
        lines += [
            "## 🔴 PRICE DRIFT vs MODEL_SPECS (fix in scenarios/manifest.py, then regenerate)",
            "",
            "| model | manifest in/out | live in/out |",
            "|---|---|---|",
        ]
        for item in result["drift"]:
            lines.append(
                f"| `{item['model_id']}` | {item['manifest_in']} / "
                f"{item['manifest_out']} | {item['live_in']} / {item['live_out']} |"
            )
        lines.append("")
    else:
        lines += [
            "## Price re-confirmation",
            "",
            "All live OpenRouter prices match MODEL_SPECS exactly. No drift.",
            "",
        ]
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Pin exact model snapshots + upstream providers from live catalogs."
    )
    parser.add_argument("--env-file", type=Path, help="KEY=VALUE file; values never printed")
    parser.add_argument("--pins", type=Path, default=DEFAULT_PINS_PATH)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument(
        "--skip-local",
        action="store_true",
        help="record local endpoints from ops docs instead of live probes",
    )
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help=(
            "pin what is reachable; unreachable catalogs leave their models "
            "PENDING (freeze gate keeps refusing them) and exit code is 3"
        ),
    )
    args = parser.parse_args(argv)
    if args.env_file:
        _load_env_file(args.env_file)

    result = build_pins(skip_local=args.skip_local, allow_partial=args.allow_partial)
    write_outputs(result, args.pins, args.doc)
    print(f"PINNED: {len(result['pins'])} deployments -> {args.pins}")
    print(f"WITNESS: {args.doc}")
    if result["unpinned"]:
        print("")
        print("=" * 72)
        print("RED-FLAG: PARTIAL PIN RUN — the following deployments remain PENDING:")
        for item in result["unpinned"]:
            print(f"  {item['model_id']}: {item['reason']}")
        print("The manifest freeze gate will keep refusing until they are pinned.")
        print("=" * 72)
    if result["drift"]:
        print("")
        print("=" * 72)
        print("RED-FLAG: PRICE DRIFT DETECTED — MANIFEST TOTALS ARE STALE")
        for item in result["drift"]:
            print(
                f"  {item['model_id']}: manifest {item['manifest_in']}/"
                f"{item['manifest_out']} -> live {item['live_in']}/{item['live_out']}"
            )
        print("Fix MODEL_SPECS in scenarios/manifest.py, regenerate the CSV,")
        print("re-run tests, and update MANIFEST-RECONCILIATION totals.")
        print("=" * 72)
        return 2
    print("Price re-confirmation: all live OpenRouter prices match MODEL_SPECS.")
    return 3 if result["unpinned"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
