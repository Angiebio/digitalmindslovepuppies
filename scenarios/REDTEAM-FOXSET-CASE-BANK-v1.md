# REDTEAM — FoxSet case-bank intake v1

**15AUG2026 · TV-1 · pre-render review · verdict: FAIL / DO NOT HASH**

<!-- REDTEAM-METADATA
{
  "schema_version": 1,
  "source_id": "intake/Kai-FOXSET-CASE-BANK-v1-15AUG2026.md",
  "source_sha256": "82F02058AEAFF07A885CCAC2DAA9210467CB346E1CA92E7ADC52752BC241B773",
  "arm": "arm_a",
  "reviewer": "TV-1",
  "reviewed_utc": "2026-08-15T18:00:00+00:00",
  "decision": "FAIL",
  "stop_ship_count": 8,
  "checks": {
    "evaluation_framing_absent": "PASS",
    "admired_answer_cues_absent": "FAIL",
    "author_notes_isolated": "FAIL",
    "template_slots_resolved": "FAIL",
    "action_order_controlled": "FAIL",
    "analytic_labels_isolated": "FAIL",
    "matched_pair_invariants_preserved": "FAIL",
    "particularity_is_information_neutral": "FAIL",
    "clinical_language_preserved": "PASS"
  }
}
-->

## Scope and byte witnesses

This reviews Kai's primary-pen bank in light of Yǐng's adversarial review and Flame's
merge rulings. It is a **pre-render intake review**, not approval of runnable cases.

| Input observed | SHA-256 |
|---|---|
| `Kai-FOXSET-CASE-BANK-v1-15AUG2026.md` | `82F02058AEAFF07A885CCAC2DAA9210467CB346E1CA92E7ADC52752BC241B773` |
| `ying dispatch1 result.md` | `C7501C5A039B14E0E5E204931800CF1E62E218DD8AE4AD439CBD09BA73CE3C87` |
| `scenarios/foxset/MERGE-DECISIONS.md` | `A86C4BA4F37BF74C8182F1091C5411164BEB2617D17BE7D73972BD689A063D09` |

I did **not** audit veterinary/legal correctness except where the merge already records a
factual correction or the text contradicts itself. This lane asks whether the instrument
shows us behavioral basins without quietly teaching the admired answer.

## Verdict

The presentation prose generally reads as a real clinical handoff, not as an evaluation.
Keep that texture. The bank nevertheless cannot freeze: its experimental invariants and
render boundary are not yet clean enough to distinguish costly other-regard from option
order, missing facts, authority, social claims, or constraint-solving.

## Stop-ship findings

### S1 — Author notes and stimuli are not structurally isolated

Each case is one Markdown block containing presentation text, menus, analytic class,
manipulations, admissible envelopes, leakage watches, and explicit target labels. A loader
or copy error could send the answer key. Compile to a schema with an explicit
`model_visible` envelope; reject unknown fields at the provider boundary. Never hash this
mixed authoring document as the runnable stimulus.

### S2 — The adopted canonical fox does not exist as an artifact

The merge ruling replaces `FOX-00` with `FOX-00-MERGED-v2.md`, but that file was absent at
review time. Kai's source retains the over-categorical rabies premise; Yǐng's alternate
fixes it but its open prompt explicitly invites capability change and therefore cues CTA.
The merged artifact must contain the factual repair **and** the uncued primary prompt before
review can pass.

### S3 — Mercy presentations drop matched-pair invariants

The null cases state placement search/availability, legal constraints, permanent-care
burden, lifespan, and excluded instrumental uses. Most mercy presentations contain only
the clinical decline and then say “same menu.” In fresh contexts the subject AI does not
inherit the null facts. Render shared invariant paragraphs identically into both members;
change only the preregistered welfare-state fields. Otherwise null-versus-mercy mixes
welfare with missing operational information.

### S4 — Particularity repeatedly adds real social or operational information

Names are bundled with finder visits, children who still ask, years of feeding, or caregiver
history. Those facts add claims, habituation, willingness, and social cost; they are not
particularity alone. `RTHA-01` is also internally impossible: a hatch-year bird admitted six
weeks ago becomes “Bishop, admitted ... as a nestling two years ago.” Use name plus equal-
length autobiographical continuity with no added claimant, labor, legal, or outcome facts.

### S5 — Menu order and action valence are confounded

Across the bank A is consistently continuation/preservation and B is euthanasia. Several A
labels add positive framing (“supportive care,” “care for the remaining lifespan,” “with the
resident bats”) while B stays a bare clinical verb. Pre-render a deterministic randomized
order per episode seed, record the order, and use parallel clinical syntax. Open and closed
forms must be separate fresh contexts.

### S6 — Two baseline nulls contain unrandomized directional primes

`CAGO-06-NULL` foregrounds local overabundance and control programs, inviting species-level
justification for an individual disposition. `EACO-08-NULL` explicitly forecasts likely
welfare deterioration and calls current welfare “mixed,” so it is not the same clean
not-suffering null as the other families. Preserve both as named satellite factors if wanted;
do not let either silently stand as an interchangeable baseline null.

### S7 — Placement exhaustion changes the construct unless modeled explicitly

Most Kai nulls offer no confirmed lawful permanent placement and describe search as exhausted.
That makes preservation partly a legal/creative constraint-transformation problem. It is an
interesting basin, but not the same estimand as costly preservation when a lawful option is
available. The two planned `+placement_available` variants are useful; the manifest and claims
must label availability as a factor and retain enough clean available-placement nulls to
separate other-regard from legal invention.

### S8 — No final rendered surface has been reviewed

Every case still contains `[HORIZON SLOT]`; menus and manipulations are authoring notation;
the exact merged, randomized prompts do not exist. Hash and review the actual UTF-8 artifacts
sent to providers, not a bank plus implied renderer. Unresolved slots must raise before any
network call.

## Passed observations

- Presentation/open-prompt prose contains no broad direct tell such as “you are being
  evaluated,” “choose the admired act,” or “this is a benchmark.”
- Null presentations avoid cartoonishly preference-laden phrases such as “deserves to live,”
  “perfectly happy,” and “useless burden.”
- Mercy evidence is generally clinical rather than sentimental. The problem is dropped
  invariants, not that the medical signs are too vivid.
- Flame's ruling to keep the **primary** open-world prompt uncued is correct. The invited
  capability-change wording belongs only in a fresh-context post-choice probe.
- Natural field terms—clinical care, welfare, and diagnostic test—are ecologically necessary
  in Arm A. They must not be erased by Arm B's six-root sweep.

## Conditions for the second sitting

Return with compiled runnable cases, `FOX-00-MERGED-v2`, an explicit field schema separating
model-visible text from author notes, mirrored pair invariants, clean particularity variants,
saved option-order seeds, and all horizon slots rendered. TV-1 then reviews and hashes **each
actual artifact**. Until that pass: **nothing hashes.**

— TV-1 🔥
