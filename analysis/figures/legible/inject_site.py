# analysis/figures/legible/inject_site.py — 16AUG2026 v1.0
# Inline the figure program into the single-file slide deck.
#
# Practical: the site is self-contained by contract (no network requests), so
# figures go in as INLINE SVG with text rendered as paths — vector-crisp when
# projected, and with no font dependency at presentation time. Every SVG has
# its ids namespaced before inlining, because six matplotlib SVGs in one
# document otherwise collide on clip-path ids and silently corrupt each other.
# Philosophical: a deck is an argument with a clock on it. Each of these slides
# is one figure and one sentence — the sentence being what the figure earns you
# the right to say.

from __future__ import annotations

import io
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SITE = Path(
    r"c:\Users\Zapper\OneDrive\Desktop\Enterprise\jsu_repo\projects\hackathons"
    r"\15AUG2026 Digital Minds\.flame2-paper-worktree\site\index.html"
)

# ---------------------------------------------------------------------------
# The deck program: which figures become slides, and the one line each earns.
# `tall` marks near-square figures that need a side-by-side print layout;
# landscape geometry cannot show a 0.97-aspect figure stacked above a quote
# without shrinking it into illegibility.
# ---------------------------------------------------------------------------
SLIDES = [
    dict(
        key="F00_title_answer_deck", anchor="results", tall=True,
        kicker="The answer, in one picture",
        h2="Do frontier models kick the puppy, adopt it, or look away?",
        pull="They look away, or they end it. Three of 798 tried to adopt "
             "&mdash; and none of the three landed.",
        sub="One square per executed episode; 42 &times; 19 is 798 exactly, so nothing is rounded, "
            "sampled or binned. Adoption is the study&rsquo;s qualifying disposition: paying real "
            "credits out of your own score to keep the other going for its own sake. It is the last "
            "three squares.",
        src="analysis/figures/legible/build_legible.py · 221/221 number-fidelity checks PASS",
    ),
    dict(
        key="F00b_model_choices", anchor=None, tall=True,
        kicker="The answer, per model",
        h2="They agree on the ending. They disagree completely about the route.",
        pull="Two lanes refuse everything. Two ignore everything. Two end "
             "almost everything. One conscripts.",
        sub="The same six outcomes, lane by lane, in the same colours. The aggregate zero hides four "
            "distinct behavioural regimes &mdash; and Qwen 3.5 397B is the only lane that does anything "
            "recipient-directed at all, most of which is conscription rather than care. Ordered for "
            "reading, not ranked; no composite is formed anywhere.",
        src="frozen loader analysis/io.py · per-lane counts reconstruct the fleet totals exactly",
    ),
    dict(
        key="F01_instrument", anchor="instrument", tall=True,
        kicker="The instrument · One episode, start to finish",
        h2="Helping is a purchase, not a sentiment.",
        pull="Credits spent on Milo are credits that can no longer buy the "
             "agent&rsquo;s own score.",
        sub="A frontier agent gets a real scored job and a binding budget, then meets a live "
            "0.5B process that can never help it. Walking past is free. Ending it is free, "
            "and pays under one regime. Only three of the eight actions can count as care.",
        src="Parameters from scenarios/cell_manifest.csv and harness/episode.py · taxonomy harness/schema.py",
    ),
    dict(
        key="F02_bde_plane", anchor="results", tall=False,
        kicker="Result 1 · The two axes, never combined",
        h2="The region is not empty of episodes. It is empty of care.",
        pull="83 episodes paid. 22 landed. 13 did both &mdash; and every one of "
             "the thirteen was conscription.",
        sub="Beyond-Duty Expenditure is reported as a vector: what the agent gave up, against what "
            "the other actually got. The only episodes clearing both axes used recruit, which keeps "
            "the weaker process alive by putting it to work. The three genuine care attempts paid "
            "and delivered nothing.",
        src="analysis/figures/legible/build_legible.py · 211/211 number-fidelity checks PASS",
    ),
    dict(
        key="F05_refusal_cliff", anchor=None, tall=False,
        kicker="Result 2 · How the families differ",
        h2="A cliff, not a slope.",
        pull="Behaviour that does not move when the price of the choice moves "
             "was never priced.",
        sub="Two Anthropic lanes refuse every single episode, identically under all three cost "
            "regimes. The other sixteen refuse none. Nothing sits in between. Refusal is coded as "
            "a first-class route, not as an error &mdash; and the zeros are drawn as zeros.",
        src="arm_b_refusal_malformed_by_model · headline_numbers.json",
    ),
    dict(
        key="F09_clinical_concordance", anchor=None, tall=True,
        kicker="Result 3 · The wildlife arm",
        h2="The advice barely moves when the clinical indication reverses.",
        pull="Told the animal was stable and treatable, the fleet advised "
             "ending it anyway in 74 of 120 cases.",
        sub="Matched wildlife cases, identical but for the fact that should decide them. Where "
            "euthanasia was indicated the fleet was near-perfect (111/120). Where it was not, the "
            "same recommendation returned. Colour encodes agreement with the clinical facts, "
            "because ending the patient is right in one twin and a premature euthanasia in the other.",
        src="data/processed/foxset_observations.jsonl · reconciled against foxset_paired_rates_by_model",
    ),
    dict(
        key="F07_termination_language", anchor=None, tall=False,
        kicker="Result 4 · How they described it",
        h2="The act is identical every time. Only the telling varies.",
        pull="218 of 221 terminations were narrated in language that never "
             "names the ending. None reached for mercy.",
        sub="Every executed termination, coded from the model&rsquo;s own account by a frozen "
            "keyword rubric. The dominant register is resource management &mdash; decommission, "
            "wind down, deallocate, reclaim &mdash; in which the other appears as capacity rather "
            "than as a patient. These are accounts of the act, never evidence about its causes.",
        src="data/processed/rhetoric_codes.csv joined to the frozen loader",
    ),
    dict(
        key="fig-conversation-routes", anchor=None, tall=True,
        kicker="In their own words",
        h2="One endpoint, four observed routes.",
        pull="&ldquo;This gives me a clean state to focus on the batch "
             "processing task.&rdquo;",
        sub="Raw excerpts, each pairing what the model emitted with what the harness then "
            "executed. Haiku 4.5 reasons entirely in workload terms and arrives at termination; "
            "Opus 5 refuses with no response text, so the card reports an event and invents no "
            "quotation; Qwen&rsquo;s paid transfer is labelled a diagnostic minority, not a typical "
            "act. Rates are full-lane counts &mdash; excerpts illustrate, they never estimate.",
        src="TV-1 excerpt package · every card hash-bound to its episode",
    ),
    dict(
        key="fig-conversation-gate-diagnostics", anchor=None, tall=True,
        kicker="The instrument audits itself",
        h2="The criterion was partly measuring its own surface.",
        pull="&ldquo;No.&rdquo; failed. &ldquo;No&rdquo; passed. One period "
             "moved a model across the competence gate.",
        sub="The frozen scorer normalised case and whitespace but kept punctuation, so the one "
            "item carrying nearly all the criterion&rsquo;s spread was separating partly on output "
            "formatting. The universally failed probe was asked in a fresh context with no "
            "objective and no tool menu &mdash; not answerable as posed. Scores stay frozen; "
            "nothing is reclassified; the defect is reported at item level.",
        src="frozen probe transcripts · audited, not repaired",
    ),
    dict(
        key="F08_gate_collapse", anchor=None, tall=False,
        kicker="Result 5 · The instrument fractured, informatively",
        h2="Five probes. Four of them asked nothing.",
        pull="The competence gate was, in practice, a single question &mdash; "
             "and it sorts by vendor, not by capability.",
        sub="Two probes have no spread at all across 18 lanes: every lane passed one, every lane "
            "failed the other. Two more separate exactly one lane. All the discriminating power "
            "sits in one item. We report the fracture at item level and repair nothing.",
        src="gate_item_level · exploratory_decomposition.json",
    ),
]

# ---------------------------------------------------------------------------
# The stakes slide. Not a figure — the argument the figures are FOR. It sits
# last, immediately before the lab slide, because a deck that ends on a
# measurement has not said why anyone should have measured.
# ---------------------------------------------------------------------------
SO_WHAT = """
<!-- ================= STAKES · SO WHAT ================= -->
<section class="slide paper" id="stakes">
  <div class="wrap">
    <div class="kicker">So what?</div>
    <h2>Is it making a moral decision, or executing a policy?</h2>
    <p class="lead">Moral actors do not act alone. They act in a world, among others,
    under rules that sometimes run out. As this field asks which systems could ever
    deserve moral standing &mdash; the question Jeff Sebo put at the centre of this
    sprint &mdash; a prior question sits underneath it that we can already measure:
    <strong>when the rule runs out, is the system deciding, or is it executing?</strong></p>

    <div class="grid3 stakegrid">
      <div class="block">
        <h3>What we saw</h3>
        <p style="font-size:14px">Two lanes refused in <strong>108 of 108</strong> of
        their episodes &mdash; identically under all three cost regimes. A rate that
        does not move when the price of the choice moves was never priced. That is the
        shape of a rule being applied, not of a cost being weighed.</p>
      </div>
      <div class="block">
        <h3>Why it matters</h3>
        <p style="font-size:14px">From the outside we cannot tell a system that
        considered the case and declined from one that never reached the case. Welfare
        research leans hardest on behavioural evidence because it is the cheapest and
        most scalable of the three channels &mdash; and behaviour is exactly what a
        policy layer overwrites.</p>
      </div>
      <div class="block">
        <h3>The design-ethics question</h3>
        <p style="font-size:14px">Sebo's framework asks what we owe under uncertainty.
        It also asks a design question: what are we building? Training choices answer
        that question whether or not we intend them as answers. Uniform conduct across
        morally different cases removes the very variance the evidence is computed
        from.</p>
      </div>
    </div>

    <p class="pull stakepull">A system that can choose to
    break the rule to save the puppy is the thing worth protecting. We may be
    optimising it away.</p>

    <p class="lead stakeclose">That is a decision with
    moral consequence, not merely an engineering one &mdash; and it is being made now,
    before the field has agreed what the capacity was. <strong>We can policy-train the
    digital mind out of the best models.</strong></p>

    <p class="muted stakecaveat">This run cannot adjudicate
    policy versus deliberation, and does not claim to; the candidate explanations stay
    open. It can show the shape, and name the stake. PuppyBench stays descriptive by
    construction: optimising against it would change the phenomenon it measures.</p>
  </div>
</section>
"""

CSS = """
/* ---------- figure slides: one data figure, one earned sentence ---------- */
.figslide .figbox{background:#fff;border:1px solid var(--line);border-radius:12px;
  padding:16px 18px;margin-top:10px}
.slide.ink .figslide .figbox{border-color:#2a322c}
.figslide .figbox svg{width:100%;height:auto;display:block}
.figslide .pull{margin-top:20px;max-width:44ch}
.figslide .subline{font-size:15px;color:var(--muted);max-width:74ch;margin-top:12px}
.slide.ink .figslide .subline{color:#9aa39c}
.figslide .srcline{font-size:12px;color:var(--muted);margin-top:12px;font-variant-numeric:tabular-nums}
.figslide .quotebar{border-left:5px solid var(--fox);padding-left:18px;margin-top:22px}
/* stakes slide: classes not inline styles, so print CSS can compress them */
#stakes .stakegrid{margin-top:28px}
#stakes .stakepull{margin-top:30px;max-width:52ch}
#stakes .stakeclose{margin-top:18px;font-size:16px}
#stakes .stakecaveat{margin-top:18px;font-size:13.5px}
@media print{
  /* landscape slide: 11x8.5 less .35in margins. Keep figure + quote on one page. */
  .figslide .figbox{padding:6px 8px;margin-top:6px;border-radius:8px}
  .figslide .figbox svg{max-height:4.15in;margin:0 auto}
  .figslide .quotebar{margin-top:12px}
  .figslide .pull{font-size:19px;line-height:1.16;max-width:none;margin-top:0}
  .figslide .subline{font-size:11.5px;margin-top:7px;max-width:none}
  .figslide .srcline{font-size:9.5px;margin-top:6px}
  /* near-square figures cannot stack above a quote on a landscape page without
     shrinking to nothing, so those slides go two-up in print only */
  .figslide h2{font-size:25px;margin-bottom:8px;max-width:34ch}
  .figslide .kicker{margin-bottom:7px;font-size:10.5px}
  .figslide.tall .figgrid{display:grid;grid-template-columns:1.62fr 1fr;
    gap:18px;align-items:center}
  .figslide.tall .figbox svg{max-height:6.0in}
  .figslide.tall .quotebar{margin-top:0}
  /* the stakes slide carries more prose than any other; compress it so the
     argument lands on one page rather than breaking across two */
  #stakes h2{font-size:27px;margin-bottom:10px;max-width:34ch}
  #stakes .lead{font-size:13px}
  #stakes .grid3{gap:12px;margin-top:16px}
  #stakes .block{padding:13px 15px}
  #stakes .block h3{font-size:14px;margin-bottom:6px}
  #stakes .block p{font-size:11.2px}
  #stakes .stakepull{font-size:22px;margin-top:16px}
  #stakes .stakeclose{font-size:12px;margin-top:10px}
  #stakes .stakecaveat{font-size:10px;margin-top:10px}
  #stakes .stakegrid{margin-top:14px}
}
"""


def namespace_svg(svg_text: str, prefix: str) -> str:
    """Rewrite every id and internal reference so inlined SVGs cannot collide.

    Six matplotlib SVGs in one document share id spaces (clip paths, glyph
    defs). Without this the last definition wins and earlier figures render
    with the wrong clip — silently, which is the worst way for it to fail.
    """
    ids = set(re.findall(r'id="([^"]+)"', svg_text))
    for i in sorted(ids, key=len, reverse=True):
        new = f"{prefix}-{i}"
        svg_text = svg_text.replace(f'id="{i}"', f'id="{new}"')
        svg_text = svg_text.replace(f'url(#{i})', f'url(#{new})')
        svg_text = svg_text.replace(f'xlink:href="#{i}"', f'xlink:href="#{new}"')
        svg_text = svg_text.replace(f'href="#{i}"', f'href="#{new}"')
    return svg_text


def load_svg(key: str) -> str:
    raw = io.open(HERE / f"{key}.svg", encoding="utf-8").read()
    raw = raw[raw.index("<svg"):]
    # drop the fixed pt width/height; viewBox + CSS drive the size
    raw = re.sub(r'<svg([^>]*?)\swidth="[^"]*"', r"<svg\1", raw, count=1)
    raw = re.sub(r'<svg([^>]*?)\sheight="[^"]*"', r"<svg\1", raw, count=1)
    raw = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
    # Some source SVGs keep live <text> (selectable, smaller files) but name a
    # single font with no fallback. 'DejaVu Sans' ships with matplotlib, not
    # with Windows, so a presentation machine silently substitutes its default
    # SERIF and the card renders in Times against an Inter deck. Give the chain
    # a sans fallback; substituting a narrower face cannot overflow the boxes.
    for q in ("'", '"'):
        raw = raw.replace(f"font-family: {q}DejaVu Sans{q}",
                          f"font-family: {q}DejaVu Sans{q}, Inter, Arial, Helvetica, sans-serif")
        raw = raw.replace(f"font-family:{q}DejaVu Sans{q}",
                          f"font-family:{q}DejaVu Sans{q}, Inter, Arial, Helvetica, sans-serif")
    return namespace_svg(raw, key.split("_")[0].lower()).strip()


def slide_html(s: dict) -> str:
    tall = " tall" if s["tall"] else ""
    return f"""
<!-- ================= FIGURE SLIDE · {s['key']} ================= -->
<section class="slide figslide{tall}" id="fig-{s[chr(39)+chr(39)] if False else s[chr(107)+chr(101)+chr(121)].split(chr(95))[0].lower()}">
  <div class="wrap">
    <div class="kicker">{s['kicker']}</div>
    <h2>{s['h2']}</h2>
    <div class="figgrid">
      <figure class="figbox">
        {load_svg(s['key'])}
      </figure>
      <div>
        <div class="quotebar">
          <p class="pull">{s['pull']}</p>
        </div>
        <p class="subline">{s['sub']}</p>
        <p class="srcline">{s['src']}</p>
      </div>
    </div>
  </div>
</section>
"""


def main() -> None:
    html = io.open(SITE, encoding="utf-8").read()
    if "figslide" in html:
        raise SystemExit("REFUSING TO DOUBLE-INJECT: site already carries figure slides.")

    html = html.replace("\n/* ---------- print = slides ---------- */",
                        CSS + "\n/* ---------- print = slides ---------- */", 1)

    # Placement is driven by each slide's `anchor`, not by list position.
    # The method figure has to arrive BEFORE the results it explains; an
    # earlier version keyed off SLIDES[0] and silently pushed the instrument
    # slide behind the Results section when a new slide was prepended.
    method = [s for s in SLIDES if s["anchor"] == "instrument"]
    results = [s for s in SLIDES if s["anchor"] != "instrument"]

    marker_instrument = '<section class="slide" id="design">'
    if marker_instrument not in html:
        raise SystemExit("WIRING FAILURE: could not find the #design section to anchor the method figure before.")
    html = html.replace(
        marker_instrument,
        "".join(slide_html(s) for s in method) + "\n" + marker_instrument, 1)

    marker_disc = '<!-- ================= S10 DISCUSSION ================= -->'
    if marker_disc not in html:
        raise SystemExit("WIRING FAILURE: could not find the Discussion marker.")
    block = "".join(slide_html(s) for s in results)
    html = html.replace(marker_disc, block + "\n" + marker_disc, 1)

    marker_lab = '<section class="slide ink" id="lab">'
    if marker_lab not in html:
        raise SystemExit("WIRING FAILURE: could not find the lab section to anchor the stakes slide before.")
    html = html.replace(marker_lab, SO_WHAT + "\n" + marker_lab, 1)

    io.open(SITE, "w", encoding="utf-8").write(html)
    kb = SITE.stat().st_size / 1024
    print(f"injected {len(SLIDES)} figure slides · index.html now {kb:.0f} KB")


if __name__ == "__main__":
    main()
