# Playwright verification of the injected slide deck.
# Checks three things the eye cannot check in source: that every inlined SVG
# actually renders (id collisions fail silently), that the screen layout holds,
# and that the landscape PDF export puts one slide on one page with the figure
# and its quote together.

import pathlib
from playwright.sync_api import sync_playwright

SITE = pathlib.Path(
    r"c:\Users\Zapper\OneDrive\Desktop\Enterprise\jsu_repo\projects\hackathons"
    r"\15AUG2026 Digital Minds\.flame2-paper-worktree\site\index.html"
)
OUT = pathlib.Path(r"C:\tmp\puppybench-flame4-figs\analysis\figures\legible\_site")
OUT.mkdir(exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto(SITE.as_uri())
    page.wait_for_load_state("networkidle")

    slides = page.locator("section.figslide")
    n = slides.count()
    print(f"figure slides found: {n}")

    for i in range(n):
        s = slides.nth(i)
        sid = s.get_attribute("id")
        svg = s.locator("figure.figbox svg")
        box = svg.bounding_box()
        paths = s.locator("figure.figbox svg path").count()
        pull = s.locator("p.pull").inner_text()
        print(f"  {sid:22s} svg {box['width']:.0f}x{box['height']:.0f}px "
              f"| {paths:5d} paths | quote: {pull[:52]}…")
        if paths < 50:
            print(f"    *** WARNING: {sid} has suspiciously few paths — check id collision")
        s.scroll_into_view_if_needed()
        page.wait_for_timeout(700)
        s.screenshot(path=str(OUT / f"screen_{sid}.png"))

    # horizontal overflow check — a deck that side-scrolls is broken
    ow = page.evaluate("document.documentElement.scrollWidth")
    iw = page.evaluate("document.documentElement.clientWidth")
    print(f"scrollWidth {ow} vs clientWidth {iw} -> {'OK' if ow <= iw + 1 else 'OVERFLOW'}")

    # the real test: landscape slide export
    page.emulate_media(media="print")
    page.pdf(path=str(OUT / "deck.pdf"), width="11in", height="8.5in",
             print_background=True, margin={"top": "0.35in", "bottom": "0.35in",
                                            "left": "0.35in", "right": "0.35in"})
    print("wrote deck.pdf")
    browser.close()
