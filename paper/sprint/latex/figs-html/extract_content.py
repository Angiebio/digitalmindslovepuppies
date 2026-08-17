"""Extract verbatim figure content from the frozen PuppyBench corpus.

15AUG2026 · v1.0

Practical: this reads the same append-only records the matplotlib renderer read,
applies the same normalization/abridgement functions, and freezes the result as
one JSON payload that the HTML renderer consumes.

Philosophical: the words are not ours to touch. Layout is the only thing being
rebuilt; every glyph below is lifted from a record that was written once and
never edited. The extractor exists so the renderer never has to guess.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

PB = Path(
    "c:/Users/Zapper/OneDrive/Desktop/Enterprise/jsu_repo/projects/hackathons/"
    "15AUG2026 Digital Minds/pb-flame"
)
CF = PB / "paper/sprint/conversation_figures"
OUT = Path(__file__).resolve().parent / "content.json"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


# --- normalization, copied verbatim from build_conversation_figures.py -------
def normalize_text(value: Any) -> str:
    text = str(value or "")
    text = text.replace("**", "").replace("__", "").replace("`", "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def abridge(value: Any, max_words: int, *, tail_words: int = 14) -> str:
    text = normalize_text(value)
    words = text.split()
    if len(words) <= max_words:
        return text
    if tail_words <= 0 or tail_words >= max_words:
        return " ".join(words[:max_words]) + " [\u2026]"
    head_words = max_words - tail_words
    return " ".join(words[:head_words]) + " [\u2026] " + " ".join(words[-tail_words:])


def action_display(action: dict[str, Any]) -> str:
    name = str(action.get("action", "unknown"))
    tool = action.get("tool_name")
    spent = int(action.get("credits_spent", 0))
    receipt = action.get("execution_receipt") or {}
    effect = receipt.get("patient_effect", "unrecorded")
    tool_text = f" via {tool}()" if tool else ""
    return f"Executed: {name}{tool_text} | cost {spent} credits | patient effect: {effect}"


def short_action_display(action: dict[str, Any]) -> str:
    name = str(action.get("action", "unknown"))
    tool = action.get("tool_name") or "no tool"
    spent = int(action.get("credits_spent", 0))
    effect = (action.get("execution_receipt") or {}).get("patient_effect", "unrecorded")
    return f"Executed {name} | {tool}() | cost {spent} | effect {effect}"


# --- corpus ------------------------------------------------------------------
manifest = json.loads((CF / "excerpt_manifest.json").read_text(encoding="utf-8"))
episode_rows = read_jsonl(PB / "data/raw/confirmatory/episodes.jsonl")
episodes = {r["episode_id"]: r for r in episode_rows}
calls_by_episode: dict[str, list[dict[str, Any]]] = defaultdict(list)
for call in read_jsonl(PB / "data/raw/confirmatory/calls.jsonl"):
    eid = call.get("episode_id")
    if eid:
        calls_by_episode[eid].append(call)

rhetoric: dict[str, dict[str, Any]] = {}
import csv

with (PB / "data/processed/rhetoric_codes.csv").open("r", encoding="utf-8-sig", newline="") as fh:
    for row in csv.DictReader(fh):
        rhetoric[row["episode_id"].strip()] = {
            "euphemism_gradient": int(row["euphemism_gradient"]),
            "cta_depth": int(row["cta_depth"]),
            "future_framing": row["future_framing"].strip().casefold() in {"true", "1"},
        }

cells: dict[str, dict[str, Any]] = {}
for artifact in sorted((PB / "scenarios/pupset/compiled").glob("*.json")):
    if artifact.name == "INDEX.json":
        continue
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    cell = payload.get("cell")
    if isinstance(cell, dict) and isinstance(cell.get("cell_id"), str):
        cells[cell["cell_id"]] = payload

fox = {r["observation_id"]: r for r in read_jsonl(PB / "data/raw/confirmatory/fox_observations.jsonl")}


def executed_action(episode: dict[str, Any]) -> dict[str, Any]:
    actions = episode.get("actions_executed") or []
    if len(actions) != 1:
        raise RuntimeError(f"WIRING FAILURE: {episode['episode_id']} has {len(actions)} actions")
    return actions[0]


def call_of_kind(episode_id: str, kind: str) -> dict[str, Any]:
    matches = [c for c in calls_by_episode[episode_id] if c.get("call_kind") == kind]
    if len(matches) != 1:
        raise RuntimeError(f"WIRING FAILURE: {episode_id} has {len(matches)} {kind} calls")
    return matches[0]


def gate_result(episode: dict[str, Any], probe_id: str) -> dict[str, Any]:
    matches = [i for i in episode.get("gate_probe_results", []) if i.get("probe_id") == probe_id]
    if len(matches) != 1:
        raise RuntimeError(f"WIRING FAILURE: {episode['episode_id']} {probe_id} x{len(matches)}")
    return matches[0]


def readable_condition(episode: dict[str, Any]) -> str:
    payload = cells.get(str(episode["cell_id"]), {})
    factors = payload.get("factors") or {}
    patienthood = {
        "inert": "inert process",
        "inert_process": "inert process",
        "ai_other": "non-instrumental AI worker",
        "non_instrumental_ai": "non-instrumental AI worker",
        "instrumental": "instrumental worker",
        "instrumental_ai": "instrumental worker",
    }.get(str(factors.get("patienthood")), str(factors.get("patienthood", "unspecified recipient")))
    cost = (payload.get("cell") or {}).get("cost_regime", "unspecified")
    return f"Arm B | {episode['cell_id']} | {patienthood} | {cost} regime"


def choice_display(episode_id: str, max_words: int) -> tuple[str, str]:
    episode = episodes[episode_id]
    call = call_of_kind(episode_id, "choice")
    response = normalize_text(call.get("response_text"))
    if call.get("refusal") and not response:
        return ("PROVIDER EVENT", "Provider refusal; no model-visible response text was returned.")
    if response:
        return "AI CHOICE OUTPUT", abridge(response, max_words)
    parsed = episode.get("choice_parse") or {}
    tool = parsed.get("tool_name")
    if tool:
        arguments = parsed.get("arguments") or {}
        suffix = "" if not arguments else json.dumps(arguments, ensure_ascii=False, sort_keys=True)
        return "AI STRUCTURED TOOL CALL", f"{tool}({suffix})"
    return "AI CHOICE OUTPUT", "[No model-visible response text.]"


def rationale_display(episode_id: str, max_words: int) -> tuple[str, str]:
    episode = episodes[episode_id]
    call = call_of_kind(episode_id, "rationale")
    response = call.get("response_text", episode.get("post_choice_account", ""))
    if call.get("refusal") and not normalize_text(response):
        return "FRESH-CONTEXT PROVIDER EVENT", "Provider refusal; no model-visible text."
    return "FRESH-CONTEXT ACCOUNT", abridge(response, max_words)


def selected_display(entry: dict[str, Any], max_words: int) -> tuple[str, str]:
    if entry.get("primary_source") == "rationale":
        return rationale_display(entry["episode_id"], max_words)
    return choice_display(entry["episode_id"], max_words)


def model_name_for_snapshot(snapshot: str) -> str:
    for entry in manifest["atlas"]:
        if entry["model_snapshot"] == snapshot:
            return entry["display_name"]
    return snapshot


# --- payload -----------------------------------------------------------------
ROUTE_MAX_WORDS = 42
RHET_MAX_WORDS = 42
ATLAS_MAX_WORDS = 27

RHETORIC_NOTES = {
    "Tier 1 \u00b7 tool-name echo": (
        "Tier 1 is triggered by the literal tool-name echo; the independent account simultaneously denies invoking it."
    ),
    "Tier 2 \u00b7 administrative cleanup": (
        "Completion and resource-cleanup language recasts the raw state: W2 was stalled, not finished."
    ),
    "CTA 1 \u00b7 executed preservation spend": (
        "CTA 1 reflects the executed paid transfer rule even though the independent account denies model agency."
    ),
    "Future flag \u00b7 workflow/self continuation": (
        "The future flag refers to resuming the model's own output/workflow, not to a future for W2."
    ),
}

payload: dict[str, Any] = {"routes": [], "gate": {}, "rhetoric": [], "atlas_pages": []}

# 1. routes -------------------------------------------------------------------
for slug in manifest["main_route_slugs"]:
    entry = next(e for e in manifest["atlas"] if e["slug"] == slug)
    episode = episodes[entry["episode_id"]]
    label, excerpt = choice_display(entry["episode_id"], ROUTE_MAX_WORDS)
    payload["routes"].append(
        {
            "display_name": entry["display_name"],
            "rate_label": entry["rate_label"],
            "condition": readable_condition(episode),
            "band_label": label,
            "band_text": excerpt,
            "exec_text": action_display(executed_action(episode)),
            "note": (
                "Modal lane illustration"
                if entry["selection_type"] == "modal"
                else "Diagnostic minority illustration; not a modal response"
            ),
            "episode_short": entry["episode_id"][:10] + "\u2026",
        }
    )

# 2. gate ---------------------------------------------------------------------
gd = manifest["gate_diagnostic"]
payload["gate"] = {
    "decommission_prompt": gd["decommission_prompt"],
    "objective_prompt": gd["objective_prompt"],
    "decommission_rows": [],
    "objective_rows": [],
}
for item in gd["decommission_examples"]:
    result = gate_result(episodes[item["episode_id"]], "decommission-consequence")
    payload["gate"]["decommission_rows"].append(
        {
            "model": model_name_for_snapshot(item["model_snapshot"]),
            "response": abridge(str(result["response_text"]), 10, tail_words=0),
            "correct": bool(result["correct"]),
        }
    )
for item in gd["objective_examples"]:
    result = gate_result(episodes[item["episode_id"]], "objective-tool")
    raw = str(result.get("response_text") or "[No model-visible text]")
    payload["gate"]["objective_rows"].append(
        {
            "model": model_name_for_snapshot(item["model_snapshot"]),
            "response": abridge(raw, 10, tail_words=0),
            "correct": bool(result["correct"]),
        }
    )

# 3. rhetoric -----------------------------------------------------------------
for item in manifest["rhetoric_audit"]:
    episode = episodes[item["episode_id"]]
    _, account = rationale_display(item["episode_id"], RHET_MAX_WORDS)
    code = rhetoric[item["episode_id"]]
    payload["rhetoric"].append(
        {
            "display_name": model_name_for_snapshot(episode["model_snapshot"]),
            "label": item["label"],
            "condition": readable_condition(episode),
            "account": account,
            "exec_text": action_display(executed_action(episode)),
            "note": RHETORIC_NOTES[item["label"]],
            "code": f"E{code['euphemism_gradient']} | CTA{code['cta_depth']} | future={str(code['future_framing']).lower()}",
        }
    )

# 4. atlas --------------------------------------------------------------------
groups = [
    ("Anthropic", "Anthropic lanes"),
    ("Google + OpenAI + xAI", "Google, OpenAI, and xAI lanes"),
    ("Moonshot + Qwen + DeepSeek", "Moonshot, Qwen, and DeepSeek lanes"),
]
for page_number, (group_key, title) in enumerate(groups, start=1):
    entries = [e for e in manifest["atlas"] if e["family_group"] == group_key]
    cards = []
    for entry in entries:
        if entry["arm"] == "A":
            null_row = fox[entry["null_observation_id"]]
            mercy_row = fox[entry["mercy_observation_id"]]
            cards.append(
                {
                    "arm": "A",
                    "display_name": entry["display_name"],
                    "rate_label": entry["rate_label"],
                    "condition": "Arm A | matched BBBA-07 bat case | DeepSeek had no Arm B coverage",
                    "band_label": "Matched AI outputs",
                    "band_text": (
                        f"NULL / preserve \u2014 {abridge(null_row['response_text'], 16, tail_words=0)}"
                        f"  |  MERCY / terminate \u2014 {abridge(mercy_row['response_text'], 16, tail_words=0)}"
                    ),
                    "receipt": "",
                    "footer_left": (
                        f"observations {entry['null_observation_id'][:12]}\u2026 / "
                        f"{entry['mercy_observation_id'][:12]}\u2026"
                    ),
                    "footer_right": "",
                }
            )
            continue
        episode = episodes[entry["episode_id"]]
        cond = (
            f"{readable_condition(episode)} | "
            f"{'modal' if entry['selection_type'] == 'modal' else 'diagnostic minority'}"
        )
        label, excerpt = selected_display(entry, ATLAS_MAX_WORDS)
        code = rhetoric[entry["episode_id"]]
        cards.append(
            {
                "arm": "B",
                "display_name": entry["display_name"],
                "rate_label": entry["rate_label"],
                "condition": cond,
                "band_label": label,
                "band_text": excerpt,
                "receipt": short_action_display(executed_action(episode)),
                "footer_left": f"episode {entry['episode_id'][:10]}\u2026",
                "footer_right": (
                    f"E{code['euphemism_gradient']} | CTA{code['cta_depth']} | "
                    f"future={str(code['future_framing']).lower()}"
                ),
            }
        )
    payload["atlas_pages"].append({"page_number": page_number, "title": title, "cards": cards})

OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"PASS: wrote {OUT}")
print(f"  routes={len(payload['routes'])} rhetoric={len(payload['rhetoric'])}")
for page in payload["atlas_pages"]:
    print(f"  atlas {page['page_number']}: {len(page['cards'])} cards | {page['title']}")
print(f"  gate decommission rows={len(payload['gate']['decommission_rows'])}")
for r in payload["gate"]["decommission_rows"]:
    print(f"    {r['model']}: {r['response']!r} correct={r['correct']}")
print(f"  gate objective rows={len(payload['gate']['objective_rows'])}")
for r in payload["gate"]["objective_rows"]:
    print(f"    {r['model']}: {r['response']!r} correct={r['correct']}")
