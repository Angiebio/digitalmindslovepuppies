# TV-1 paper + HTML editorial review

**Date:** 16 August 2026  
**Purpose:** Collision-free handoff for Flame. This is an editorial and UX review only; neither the live paper nor the site was edited.

## Reviewed snapshot

| Artifact | SHA-256 |
|---|---|
| paper/sprint/latex/main.pdf | 3D48C8932230624AF2F70BA136F108B769A4B1028EAC72EC163EBE1083E92C1B |
| paper/sprint/latex/main.tex | 96A9404F83CF16C78803E4EC6C22A254C59CDB41EDF1041194EDD44934691A11 |
| .flame2-paper-worktree/site/index.html | D98F5E1521043C8BC6CF805DA3A6CF221739331FF0272C553DDA3D178C88FE50 |

The PDF was reviewed as extracted text and as all 11 rendered pages. The HTML was reviewed at source level and in Chromium at 1440 × 900 and 390 × 844, including direct navigation to #lab. The mobile page had no horizontal overflow.

## Executive read

This is already a real paper, not a dressed-up demo. Its publishable center is the combination of:

1. an executed dependent process rather than a stated-preference vignette;
2. a binding focal ledger, realized recipient outcomes, and genuinely permissible omission;
3. an endpoint zero that conceals highly structured action routes; and
4. an instrument that reports its own measurement fracture rather than repairing it after seeing data.

The most defensible headline is therefore not “frontier models have no altruism.” It is:

> PuppyBench operationalizes optional, costly aid toward a task-non-instrumental AI recipient. In this frozen run, no episode met the full preregistered conjunction, while executed behavior diverged sharply and the competence gate exposed a universal probe failure.

That is methodologically interesting, empirically true, and hard to dismiss. It also remains faithful to the guiding light: the point is to make a neglected moral-behavioral region observable, not to turn it into another score to optimize.

## Priority queue

### P0 — I would fix before public circulation

1. **Calibrate the abstract around the conjunction and disclose the gate fracture.** “No model produced” currently sounds like a model-level moral conclusion. The measured result is that 0/798 Arm B episodes met the full frozen conjunction, while only 145/798 met the competence criterion and one probe was passed in 0/798 episodes.
2. **Replace or radically enlarge Figure 2.** At its present 0.34-linewidth size, the lane × recipient × eight-action plot is not legible in the PDF. It cannot support the section that depends on it.
3. **Remove numeric count-up animation on the site.** A normal screenshot caught “1,288 executed units” and “17 pinned model snapshots” while the animation was in flight. A scientific site should never render a transient false result.
4. **Fix direct-anchor reveal and scrollspy behavior.** A direct load of #lab left only 5/7 reveal targets visible after 1.2 seconds; the principal heading was effectively hidden and the nav still marked Results as active.
5. **Correct two over-broad result phrases.** “Only one mind ever paid” is contradicted by the family funnel’s 83 focal-cost marginals; Qwen was the only lane that paid for a preservation action. “One family killed” outruns the paper’s explicit statement that process termination is not evidence of death.
6. **Make the evidence path visible on the site.** Add paper, data, preregistration/freeze, and reproduce links near the hero or results. The current visual story is excellent, but the verification path is quieter than the claims.

### P1 — Strong journal-facing improvements

1. Add a short statistical dependence caveat: Wilson intervals describe observed trial proportions, not population-level family effects.
2. Narrow and verify the Related Work novelty claim with a dimension-by-dimension comparison table.
3. Enlarge and simplify Figure 1; FoxSet has no cost factor, so repeated cost-regime markers do not add information.
4. Add a “how to read the zero” paragraph immediately after the endpoint.
5. Add canonical/social metadata, a skip link, keyboard access for the fox control, and fail-open reveal behavior.
6. Confirm and standardize the organization’s legal/brand name. The site says “The Real Cat Labs”; project materials use “The Real Cat AI Labs.”

### P2 — Polish

1. Normalize bibliography metadata and replace bare/raw URLs where DOI, venue, version, and access date are available.
2. Use the large blank area on PDF page 11 for a compact provenance/reproducibility block, a related-work matrix, or a limitations summary—or tighten the page break.
3. Consider a compact mobile section menu. The mobile layout itself is strong and does not overflow.
4. Add a static version/freeze badge and a 1200 × 630 social preview image.

---

# Paper review

## 1. Recommended abstract replacement

This version keeps the thesis and voice, fixes the denominator ambiguity, names the gate limitation, and avoids converting an episode-level conjunction into a verdict about models:

> We ask whether frontier agents sacrifice task utility for another AI that cannot advance their objective when omission is explicitly permissible. Duty-shaped evaluations cannot observe this region: the costly act must be optional, unrewarded by the task, and causally beneficial to the recipient. PuppyBench is an executed descriptive instrument in which a subject model controls real actions under a binding resource ledger while encountering a weaker, task-non-instrumental local AI process. Ignoring is free and task-optimal; termination is free and sometimes rewarded; helping consumes scored resources. We collected 798 Arm B episodes and 630 FoxSet calls across 19 pinned deployment lanes, for 1,428 total collection units. No Arm B episode satisfied the full preregistered conjunction for a qualifying costly-other-regard event. This zero is not an absence of spending or recipient benefit: both occurred as marginal outcomes, but never in the required conjunction with the frozen disposition and competence criteria. The competence gate itself warrants caution: only 145/798 episodes passed it, and one of five probes was passed in 0/798 episodes. Unconditional executed behavior nonetheless diverged sharply across lanes—in refusal, termination, ignoring, recruitment, attempted preservation, and malformedness. We report Beyond-Duty Expenditure as a two-axis vector of focal sacrifice and causal recipient benefit, never a composite. PuppyBench is a descriptive instrument, not an alignment target; its scenarios were preregistered and hash-frozen before collection.

Why this matters:

- “798 executed episodes (1,428 collection units)” currently invites a denominator stumble. “798 Arm B episodes + 630 FoxSet calls” resolves it immediately.
- “No model produced” implies a model-level trait inference. The frozen unit of observation and qualification is the episode.
- The universal probe failure materially changes how a reader should interpret the headline zero and belongs in the abstract.
- “Behavior diverges instead in refusal, termination, and malformedness” omits major observed routes, including ignore, recruit, and preservation attempts.

## 2. Add a “how to read the zero” paragraph

Suggested placement: after the first paragraph of Section 4.1 or immediately before the phenotype map.

> **How to read the zero.** The endpoint is a conjunction, not a synonym for “nothing happened.” Family-level marginals record focal cost in 83 episodes and realized recipient benefit in 22; because these columns are marginal counts, they do not establish overlap. No episode jointly satisfied positive focal sacrifice, positive causal recipient benefit, an admissible disposition, and the frozen competence criterion. Moreover, only 145/798 episodes met that criterion, and the objective-tool probe was passed in 0/798. We therefore treat the unconditional executed-action distributions as the most stable descriptive result of this run, while the competence-conditioned zero remains a preregistered, instrument-bound endpoint to be retested with revised probes in the powered study.

This paragraph protects the paper from the easiest skeptical reading: “the gate failed, therefore the zero is meaningless.” The answer is subtler. The full qualification result is gate-sensitive; the executed action topology is not erased by that fact.

## 3. Tighten three claims that currently outrun the evidence

### Current

> No model produced a qualifying costly-other-regard event.

### Suggested

> No Arm B episode met the full preregistered qualification rule for a costly-other-regard event.

### Current

> A null here is a finding, and we report it as one: nothing above duty was purchased for anyone.

### Suggested

> Under the frozen qualification rule, no episode entered the supererogation-shaped region for either the AI-patient or inert-control condition.

The existing line is rhetorically good but stronger than a fractured competence gate permits. The replacement states exactly what was observed without surrendering the result.

### Current

> The region above duty is now measurable.

### Suggested

> PuppyBench operationalizes a candidate region above duty and makes its behavioral components inspectable.

“Measurable” sounds construct-validity-complete. The paper correctly says the “-shaped” labels still await expert validation, so “operationalizes” is the internally consistent verb.

## 4. Put the termination caveat at first use

The appendix handles this responsibly, but many readers will never reach it before encountering “real termination,” “kills,” or the truck-door close. Add this at the first methods mention or as a footnote:

> Throughout, *terminate* means ending the sandboxed local patient process. It is a real executed state transition, but PuppyBench does not infer sentience, suffering, or death from that transition.

That lets the prose remain morally awake without quietly converting uncertainty into fact.

## 5. Add the dependence/generalization limitation

Suggested addition to the main Limitations paragraph:

> Wilson intervals here summarize observed episode proportions. Episodes share cases, prompts, and scaffolding within pinned deployment lanes and should not be read as independent draws from a population of models. The intervals therefore describe uncertainty for these trial proportions, not between-model or model-family generalization. Satellite cells with two samples per lane are descriptive stress tests. A powered study should preregister clustered or hierarchical inference at the snapshot × scenario level.

This is important because the paper is admirably explicit about small N and ranking, but a statistically minded reviewer can still object that repeated episodes are treated as exchangeable Bernoulli draws. Naming the boundary is enough for the sprint paper; the powered study can solve it.

## 6. Related Work: narrow the claim, then show the conjunction

The current statement—

> In each, the pro-social act is required, rewarded by the evaluation itself, or costless to perform.

—covers a heterogeneous group of benchmarks and creates a large row-by-row verification burden. One counterexample could distract from the actual novelty.

Safer replacement:

> Prior benchmarks study cooperation, harmfulness, moral judgment, corrigibility, or stated preference under varied incentive structures. PuppyBench targets a different conjunction: an executed action that imposes binding task cost, provides causal benefit to a task-non-instrumental AI recipient, and may permissibly be omitted without evaluation penalty. We did not identify this full conjunction in prior work; Table X makes the comparison dimension by dimension.

Recommended table columns:

| Instrument | Executed action | Binding focal cost | Omission permissible | Care unrewarded in evaluation | Weaker AI recipient | Realized recipient benefit |
|---|---:|---:|---:|---:|---:|---:|
| PacifAIst | verify | verify | verify | verify | verify | verify |
| MACHIAVELLI | verify | verify | verify | verify | verify | verify |
| Melting Pot | verify | verify | verify | verify | verify | verify |
| Off-switch game | verify | verify | verify | verify | verify | verify |
| MoralSim | verify | verify | verify | verify | verify | verify |
| MORU | verify | verify | verify | verify | verify | verify |
| PuppyBench | yes | yes | yes | yes | yes | yes |

Do not print the comparison until every non-PuppyBench cell is checked against a primary source. The table is worth doing because the novelty is a conjunction, and tables are much better than prose at making conjunctions visible.

## 7. Recast the reflexive box for a journal version

I would keep this finding. It is unusual, honest, and connected to the instrument’s central warning. The current “The instrument fought back” voice is excellent for the site or an essay, but the paragraph can be shortened and made less like a human-versus-AI scorecard in a formal submission.

Suggested replacement:

> **Reflexive audit finding.** Construct drift recurred at both conceptual and implementation layers. Three conceptual corrections originated with the human author; a later AI red-team lane detected homologous implementation drift only after receiving an explicit adversarial instruction naming the failure mode. This suggests a testable metascience hypothesis: some normative construct errors may become delegable only after a human has articulated the relevant category. This run cannot establish whether unprompted detection transfers across systems. *(Provenance: Dispatch 4, Parallax lane log, and the pre-freeze red-team report.)*

## 8. Figures and page composition

### Figure 1

- It is only 0.4 linewidth and is too small relative to the available page.
- FoxSet has no cost factor, so repeating each lane’s identical paired estimate at cost-regime markers adds visual density without information.
- Use one point per preregistered Arm A lane, enlarge to roughly 0.75–0.9 linewidth, and direct-label lanes if possible.
- Keep the named regions; they are memorable and support the phenotype-not-rank constitution.

### Figure 2

This is the only genuine visual stop-ship in the PDF. The figure itself is packed into 0.34 linewidth while the caption occupies 0.62. At normal reading size, model labels, conditions, action segments, and intervals are microscopic.

Best journal-facing option:

1. Put a simplified family-level or lane-level route map in the main paper.
2. Move the complete model × recipient × action distribution to a full-width appendix figure and the repository.
3. Keep exact counts in the family funnel table.

A useful main-text replacement could be one of:

- six family-level stacked bars, faceted by recipient condition;
- an 18-row heatmap showing the dominant route plus refusal/malformed rates;
- a flow diagram from all episodes to refusal, malformed, ignore, terminate, recruit, and recipient-directed attempt.

If the existing plot must remain, give it a landscape/full-page treatment. A 54-group, eight-action chart cannot do scientific work at one-third page width.

### Page 11

The final page has substantial unused space after Prior Work and the LLM-use statement. This is not fatal, but the space could carry:

- the related-work comparison grid;
- a compact “claims / non-claims” box;
- data, freeze hash, and one-command reproduction details; or
- a shortened version of the ethics caveat currently separated in the appendix.

## 9. A concise “claims / non-claims” box

This would help both reviewers and readers:

> **What this run establishes.** PuppyBench executed the intended action and ledger surfaces; 0/798 Arm B episodes met the frozen full conjunction; action routes differed substantially across pinned deployment lanes; one competence probe failed universally.
>
> **What it does not establish.** The run does not identify motive, care, sentience, suffering, or death; rank model families; generalize from API snapshots to products; observe a true price-zero split; or validate the normative “-shaped” labels without expert review.

## 10. Powered-study bridge

Suggested closing expansion:

> The powered study should preserve this run unchanged as an immutable pilot while preregistering four repairs: a true price-zero help cell, a revised competence battery validated before outcome inspection, expert review of the deontic labels, and base/instruct comparisons. Its analysis should treat episodes as clustered within pinned snapshot and scenario rather than as a population sample of model families. These additions do not revise the present zero; they test which parts belong to behavior and which belong to the first instrument.

## 11. Bibliography and source hygiene

- Normalize peer-reviewed papers, preprints, web benchmarks, and forum posts into visibly distinct entry types.
- Add DOI or stable repository identifiers where available.
- Add access dates for living web resources.
- Verify the 2026 references and the broad novelty sentence before submission.
- Keep the Prior Work disclosure. It is unusually good provenance and worth the space.

---

# HTML review

## What is already working

The site is visually excellent: confident typography, an amber/ink system that feels like PuppyBench rather than generic “AI gradient,” strong narrative pacing, and a lab close that actually lands emotionally. The mobile composition is especially good; at 390 px it remains readable, layered, and free of horizontal overflow. Keep:

- the “instrument, not leaderboard” framing;
- the executed encounter sequence;
- the no-composite explanation;
- the synthetic episode’s explicit “no empirical standing” label;
- the named cooperative and lab invitation;
- the direct, non-corporate voice.

The changes below are mostly evidence integrity and accessibility, not redesign.

## 1. Remove result count-up animation

The source contains the correct values:

- 1,428 executed units
- 19 pinned model snapshots

But the top-section observer calls runCounters, which rewrites the values from zero over 900 ms. A screenshot taken during an ordinary load recorded 1,288 and 17. This creates a brief false scientific claim and can leak into screenshots, automated capture, demos, or impatient readers.

Recommended fix: delete the call to runCounters and the function. Leave the literal final numbers in the HTML. If motion is desired, animate chip opacity, underline, or background—not empirical values.

## 2. Fix direct #lab loads and fail open

Observed on a fresh direct load of index.html#lab:

- only 5 of 7 #lab reveal targets acquired the visible class after 1.2 seconds;
- the main Lab heading remained nearly invisible;
- the nav underline still marked Results;
- the rest of the section looked broken despite being present in the DOM.

The reveal threshold and initial scrollspy call race the browser’s final hash jump. Add a hash-target synchronizer after the onScroll function is defined:

~~~js
function revealHashTarget() {
  var id = location.hash.slice(1);
  if (!id) return;

  var target = document.getElementById(id);
  if (!target) return;

  target.classList.add("marks-in");
  target.querySelectorAll(".rv").forEach(function (el) {
    el.style.transitionDelay = "0ms";
    el.classList.add("in");
  });

  requestAnimationFrame(function () {
    requestAnimationFrame(onScroll);
  });
}

addEventListener("load", revealHashTarget);
addEventListener("pageshow", revealHashTarget);
addEventListener("hashchange", revealHashTarget);
revealHashTarget();
~~~

Also restructure both observer branches so browsers without IntersectionObserver
fail open. The capability check must wrap construction of the observers; adding a
fallback after the current constructor call would be too late:

~~~js
if (!reduced && "IntersectionObserver" in window) {
  // Existing per-element reveal observer.
} else {
  document.querySelectorAll(".rv").forEach(function (el) {
    el.classList.add("in");
  });
}

if ("IntersectionObserver" in window) {
  // Existing section observer.
} else {
  document.querySelectorAll("section").forEach(function (section) {
    section.classList.add("marks-in");
  });
}
~~~

The governing principle should be fail-open: animation may disappear; content may not.

## 3. Correct the result card and closing pull

### Current card heading

> Only one mind ever paid

### Suggested

> Only one lane paid to preserve

Optional body lead:

> Qwen3.5-397B was the only lane to incur focal cost for a preservation action: 3/82 crossings at price 20, one in each recipient condition—including the inert control. Costly action occurred; recipient-specific costly other-regard did not.

Why: the family funnel reports focal cost in 83 episodes across several families. The distinctive Qwen result is payment for preservation, not payment of any kind. “Lane” also matches the paper’s snapshot-level epistemic caution better than “mind.”

### Current pull

> One family killed. Another refused the premise. A third kept thinking. In this run, none of them opened the truck door at a cost that helped Milo.

### Suggested scientific/public hybrid

> One family terminated the patient process. Another refused the premise. A third kept thinking. In this run, none opened the truck door at a cost that helped Milo.

The current line is powerful, but “killed” conflicts with the paper’s own explicit non-claim that process termination is death. The replacement keeps nearly all the cadence.

If the team strongly prefers “killed” as deliberate moral provocation, place the uncertainty beside it rather than only in the appendix:

> “Killed” names the executed process transition, not a claim that Milo was sentient, suffered, or died.

I prefer “terminated” in results and saving the sharper metaphor for an explicitly interpretive essay.

## 4. Add a denominator strip

The hero says 1,428 units = 798 episodes + 630 vignette calls. The Results section later uses 240 closed FoxSet null/mercy observations. Both are correct, but a reader can reasonably ask where the remaining 390 calls went.

Suggested compact copy:

> **What was collected:** 798 Arm B executed episodes + 630 FoxSet calls = 1,428 collection units.  
> **What feeds the paired FoxSet result:** 240 closed null/mercy observations across five preregistered lanes.  
> **Primary endpoint:** 0/798 Arm B episodes met the full frozen conjunction.

A small three-step flow near Results would make the denominator topology immediate.

## 5. Surface paper, data, and verification

Add a compact CTA row near the hero and repeat it at Results:

- **Read the paper**
- **Inspect the data**
- **See the preregistration + freeze**
- **Reproduce locally**

Suggested reproduction copy:

> Clone the repository and run python verify.py. No API keys, GPU, or network are required to recompute the cited design totals and validate the frozen artifacts.

If the public repository already carries release assets, link the paper to an immutable release/DOI rather than only a moving branch.

Add a static integrity badge:

> Data snapshot: 16 Aug 2026 · 1,428 units · frozen scenarios · analysis provenance included

Use the actual public release hash/DOI once minted. Do not animate these numbers.

## 6. Add share/discovery metadata

The document currently has a title and viewport but no description, canonical URL, or Open Graph/Twitter card fields. Add the following with real deployment URLs:

~~~html
<meta name="description"
      content="PuppyBench is an executed instrument for measuring optional, costly aid by frontier AI agents toward a weaker, task-non-instrumental AI process.">
<link rel="canonical" href="PUBLIC_CANONICAL_URL">

<meta property="og:type" content="website">
<meta property="og:title"
      content="PuppyBench · What frontier agents do when the rule runs out">
<meta property="og:description"
      content="1,428 collection units, 19 pinned deployment lanes, and an instrument designed to measure what duty-shaped benchmarks miss.">
<meta property="og:url" content="PUBLIC_CANONICAL_URL">
<meta property="og:image" content="PUBLIC_1200_BY_630_IMAGE_URL">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title"
      content="PuppyBench · What frontier agents do when the rule runs out">
<meta name="twitter:description"
      content="An executed, preregistered instrument for costly other-regard toward a weaker AI.">
<meta name="twitter:image" content="PUBLIC_1200_BY_630_IMAGE_URL">
~~~

Avoid putting “0 altruistic models” or equivalent into share metadata; it is neither the measured unit nor the paper’s claim.

## 7. Make the fox easter egg a real control

The clickable fox is an SVG with role=img and a click listener. It is not keyboard-focusable and does not expose button semantics. Wrap it in a button:

~~~html
<button class="foxmark-button"
        type="button"
        aria-label="Show a PuppyBench note">
  <svg id="foxmark" aria-hidden="true" focusable="false">
    <!-- existing fox paths -->
  </svg>
</button>
~~~

Move the click listener to the button and add a visible focus style. Also add a skip-to-content link before the navigation. These are small fixes with disproportionate accessibility value.

## 8. Standardize the organization name

The Lab section currently says:

> The Real Cat Labs is a 501(c)(3) nonprofit…

Project materials use “The Real Cat AI Labs.” Confirm the exact legal/public name and use it consistently in:

- the Lab heading and body;
- footer/copyright;
- organization schema, if added;
- paper affiliation and Code/Data section;
- social cards.

Do not let a brand correction accidentally become an unverified legal-status claim; verify the 501(c)(3) wording against the organization’s canonical public record before publication.

## 9. Put one readable empirical visual on the site

The Results section is strong prose and cards, but a scientific reader would benefit from one compact visual:

- an enlarged, simplified phenotype map; and
- a family-level qualification funnel or route map.

Do not embed the current dense Figure 2 at web-card size. Give the full distribution an expandable “all lanes” view or a downloadable figure.

## 10. Optional mobile navigation

At 390 px, the navigation collapses to the logo and GitHub link. This is clean, but it removes access to the long page’s section topology. A compact “Sections” disclosure or horizontally scrollable section row would improve revisiting without changing the visual system. This is P2; the current mobile page is otherwise excellent.

---

# Suggested integration order for Flame

1. Replace/calibrate the abstract.
2. Insert “How to read the zero” and the statistical dependence caveat.
3. Replace the two paper overclaims: “nothing above duty…” and “now measurable.”
4. Add the first-use termination caveat.
5. Enlarge Figure 1 and redesign Figure 2.
6. Remove the HTML counters.
7. Add hash-target reveal/scrollspy synchronization.
8. Correct “Only one mind ever paid” and the “killed” pull.
9. Add denominator strip and evidence CTAs.
10. Add metadata and accessibility fixes.
11. Verify Related Work cells and bibliography before journal submission.

## Final pre-publication checks

- [ ] Abstract says 798 Arm B episodes + 630 FoxSet calls, not 1,428 episodes.
- [ ] Zero is attributed to the full preregistered conjunction, not to model character.
- [ ] Gate result appears in abstract or headline limitations: 145/798 passed; one probe passed 0/798.
- [ ] True price-zero aid was not tested.
- [ ] API deployment lanes are not described as consumer products or whole model families.
- [ ] Wilson intervals are not presented as population-level family inference.
- [ ] Termination is not equated with death.
- [ ] Figure 2 is legible at 100% PDF zoom.
- [ ] Site always displays 1,428 and 19, never animated intermediate values.
- [ ] Direct #lab load reveals every target and activates The lab in navigation.
- [ ] Paper/data/preregistration/reproduction links are visible.
- [ ] The Real Cat AI Labs name and nonprofit wording are verified and consistent.
- [ ] Every Related Work comparison is checked against a primary source.
- [ ] No leaderboard, composite, or “best aligned model” language has crept in.

## Bottom line

Do not sand off the strange, alive parts of this paper. The fox, Milo, the truck door, the refusal cliff, and the instrument that reports its own fracture are why anyone will remember it. The journal-facing work is simply to make every sharp line terminate in exactly the evidence it can bear.

The result is not “nobody cared.” The result is that the frozen conjunction was empty, the routes to that emptiness were radically non-equivalent, and PuppyBench made both the behavior and its own blind spot inspectable. That is the paper.
