"""
Generate EtsyPulse slide deck PDF using reportlab + Pillow.
Matches the PPTX brand palette precisely.
"""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from PIL import Image as PILImage
import io

OUT_MAIN  = Path("docs/submission/slides/etsypulse-slides.pdf")
OUT_FINAL = Path("docs/submission/final/etsypulse-slides.pdf")
SHOTS_DIR = Path("docs/submission/screenshots")

# ── Page size: 10" × 5.625" (16:9) ──────────────────────────────────────────
PW = 10 * inch
PH = 5.625 * inch

# ── Palette ──────────────────────────────────────────────────────────────────
CREAM    = HexColor("#FFF7EA")
PARCH    = HexColor("#EFE2CF")
INK      = HexColor("#21160F")
SOIL     = HexColor("#5B3B27")
MUTED    = HexColor("#907060")
COPPER   = HexColor("#B4572D")
COPPDK   = HexColor("#78361E")
SAGE     = HexColor("#6F8663")
GOLD     = HexColor("#D59A38")
LINE     = HexColor("#D4B8A0")
DARK     = HexColor("#2A1A08")
DKTEXT   = HexColor("#C8A882")


def try_register_font(name, path, bold_path=None):
    try:
        pdfmetrics.registerFont(TTFont(name, path))
        if bold_path:
            pdfmetrics.registerFont(TTFont(f"{name}-Bold", bold_path))
        return True
    except Exception:
        return False


# Try to register some fonts; fall back to Helvetica/Times
_FONT_PATHS = [
    "/usr/share/fonts/truetype/lato/Lato-Regular.ttf",
    "/usr/share/fonts/truetype/lato/Lato-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

SANS = "Helvetica"
SANS_B = "Helvetica-Bold"
SERIF = "Times-Roman"
SERIF_B = "Times-Bold"
MONO = "Courier"

if Path("/usr/share/fonts/truetype/lato/Lato-Regular.ttf").exists():
    try_register_font("Lato", "/usr/share/fonts/truetype/lato/Lato-Regular.ttf",
                      "/usr/share/fonts/truetype/lato/Lato-Bold.ttf")
    SANS = "Lato"; SANS_B = "Lato-Bold"


class Slide:
    def __init__(self, c: canvas.Canvas):
        self.c = c

    def bg(self, color=None):
        if color is None: color = CREAM
        self.c.setFillColor(color)
        self.c.rect(0, 0, PW, PH, fill=1, stroke=0)

    def rule(self, color, height=4, y=PH):
        self.c.setFillColor(color)
        self.c.rect(0, y - height, PW, height, fill=1, stroke=0)

    def rect_f(self, x, y, w, h, fill, stroke=None, sw=0):
        # y from top
        ry = PH - y - h
        self.c.setFillColor(fill)
        if stroke:
            self.c.setStrokeColor(stroke)
            self.c.setLineWidth(sw or 1)
            self.c.rect(x * inch, ry, w * inch, h * inch, fill=1, stroke=1)
        else:
            self.c.rect(x * inch, ry, w * inch, h * inch, fill=1, stroke=0)

    def text(self, txt, x, y, size=12, font=None, color=None, align="left"):
        if not font: font = SANS
        if not color: color = INK
        self.c.setFont(font, size)
        self.c.setFillColor(color)
        rx = x * inch
        ry = PH - y * inch
        if align == "center":
            self.c.drawCentredString(rx, ry, txt)
        elif align == "right":
            self.c.drawRightString(rx, ry, txt)
        else:
            self.c.drawString(rx, ry, txt)

    def text_box(self, lines, x, y, w, size=12, font=None, color=None,
                 leading=None, align="left"):
        """Draw multiple lines of text, top-down."""
        if not font: font = SANS
        if not color: color = INK
        if not leading: leading = size * 1.4
        self.c.setFont(font, size)
        self.c.setFillColor(color)
        for i, line in enumerate(lines):
            ry = PH - y * inch - i * leading
            rx = x * inch
            if align == "center":
                self.c.drawCentredString(rx + w * inch / 2, ry, line)
            else:
                self.c.drawString(rx, ry, line)

    def pill(self, label, x, y, w, h, bg, fg, size=9):
        self.rect_f(x, y, w, h, bg)
        cx = (x + w / 2) * inch
        self.c.setFont(SANS_B, size)
        self.c.setFillColor(fg)
        self.c.drawCentredString(cx, PH - (y + h * 0.6) * inch, label)

    def image(self, path, x, y, w, h):
        try:
            img_path = str(path)
            # Use reportlab's drawImage
            self.c.drawImage(img_path, x * inch, PH - (y + h) * inch,
                             w * inch, h * inch, preserveAspectRatio=True,
                             anchor='nw', mask='auto')
        except Exception as e:
            # Draw placeholder
            self.rect_f(x, y, w, h, PARCH, LINE, 1)
            self.text("[screenshot]", x + w/2, y + h/2, 10, SANS, MUTED, "center")

    def eyebrow(self, text_str, x=0.5, y=0.32, color=None):
        if not color: color = COPPER
        self.text(text_str, x, y, 8, SANS_B, color)

    def headline(self, text_str, x=0.5, y=0.85, size=28, color=None, font=None):
        if not color: color = INK
        if not font: font = SERIF_B
        # Handle multi-line via newline split
        lines = text_str.split("\n")
        leading = size * 1.12
        for i, line in enumerate(lines):
            self.text(line, x, y + i * (leading / 72), size, font, color)

    def section_label(self, label, color=None, x=0.5, y=0.3):
        if not color: color = COPPER
        self.c.setFont(SANS_B, 8)
        self.c.setFillColor(color)
        # Letter-spaced manually
        self.c.drawString(x * inch, PH - y * inch, label)

    def card_dark(self, x, y, w, h):
        self.rect_f(x, y, w, h, DARK)

    def left_accent(self, x, y, h, color=None):
        if not color: color = COPPER
        self.rect_f(x, y, 0.05, h, color)


def slide_1(s: Slide):
    """Cover — dark left panel, cream right with brief card."""
    s.bg(CREAM)

    # Left dark panel
    s.rect_f(0, 0, 5.5, 5.625, INK)
    # Copper top rule
    s.rect_f(0, 0, 5.5, 0.05, COPPER)

    # Eyebrow — raised so it clears the headline ascenders
    s.text("ETSYPULSE  ·  AUTONOMOUS MARKET DESK", 0.45, 0.26, 7.5, SANS_B, COPPER)

    # Headline — pushed down to give the eyebrow breathing room
    s.text("Market signals,", 0.45, 0.90, 36, SERIF_B, CREAM)
    s.text("not market noise.", 0.45, 1.52, 36, SERIF_B, CREAM)

    # Tagline — extra gap from the headline so it clears the descenders
    s.text("Set the shop once. Agents monitor.", 0.45, 2.36, 13, SANS, HexColor("#EFE2CF"))
    s.text("Only actionable briefs land.", 0.45, 2.56, 13, SANS, HexColor("#EFE2CF"))

    # Sub
    s.text("EtsyPulse: Autonomous Market Intelligence for Etsy Sellers", 0.45, 2.94, 9.5, SANS, MUTED)

    # Pills
    pills = [("Powered by Bright Data", COPPER, CREAM), ("7 AI Agents", COPPDK, CREAM), ("FastAPI + React", INK, DKTEXT)]
    for i, (lbl, bg, fg) in enumerate(pills):
        s.pill(lbl, 0.45 + i * 1.68, 4.7, 1.55, 0.3, bg, fg, 8)

    # Right: brief card
    cx, cy, cw, ch = 5.75, 0.38, 3.95, 4.9
    s.rect_f(cx, cy, cw, ch, HexColor("#2A1A10"))
    s.rect_f(cx, cy, cw, 0.04, HexColor("#3A2618"))

    # "BRIEF" badge
    s.rect_f(cx + 0.22, cy + 0.22, 0.72, 0.25, HexColor("#2A4030"))
    s.text("BRIEF", cx + 0.36, cy + 0.44, 8, SANS_B, SAGE)

    # Judge badge
    s.rect_f(cx + 1.02, cy + 0.22, 1.1, 0.25, HexColor("#3A2A10"))
    s.text("Judge  82%", cx + 1.08, cy + 0.44, 8, MONO, GOLD)

    # Brief title
    s.text("Refresh gift positioning on", cx + 0.22, cy + 0.72, 12.5, SANS_B, HexColor("#FFE8CC"))
    s.text("'personalized necklace' — act this week", cx + 0.22, cy + 0.95, 12.5, SANS_B, HexColor("#FFE8CC"))

    # Score bars
    bars = [("Actionability", 0.88), ("Urgency", 0.74), ("Evidence", 0.84)]
    for i, (lbl, pct) in enumerate(bars):
        by = cy + 1.3 + i * 0.38
        s.text(lbl, cx + 0.22, by + 0.17, 9, SANS, DKTEXT)
        s.rect_f(cx + 1.38, by + 0.04, 1.9, 0.1, HexColor("#3A2A18"))
        if pct > 0:
            s.rect_f(cx + 1.38, by + 0.04, 1.9 * pct, 0.1, COPPER)
        s.text(f"{int(pct*100)}%", cx + 3.35, by + 0.17, 9, MONO, GOLD)

    # Actions
    s.text("RECOMMENDED ACTIONS", cx + 0.22, cy + 2.65, 7, SANS_B, HexColor("#806050"))
    actions = [
        "→  Update listing titles with gift-occasion keywords",
        "→  Refresh hero photos with gift-ready styling",
        "→  Create a curated gift bundle collection",
    ]
    for i, a in enumerate(actions):
        s.text(a, cx + 0.22, cy + 2.88 + i * 0.25, 9, SANS, DKTEXT)

    # Why now
    s.rect_f(cx + 0.22, cy + 3.72, cw - 0.44, 0.008, HexColor("#4A3020"))
    s.text("View full brief  →", cx + 0.22, cy + 4.0, 9.5, SANS_B, COPPER)

    # BD source line
    s.text("Data: Bright Data Web Unlocker  ·  web_data_etsy_products  ·  NVIDIA NIM",
           cx + 0.22, cy + 4.65, 7.5, MONO, HexColor("#60402A"))


def slide_2(s: Slide):
    """Problem."""
    s.bg(CREAM)
    s.rule(COPPER, 4)
    s.section_label("THE PROBLEM", COPPER)
    s.headline("Etsy sellers are swimming in\nsignals, drowning in tabs.", 0.5, 0.75, 24)

    problems = [
        ("Competitor repricing", "Competitors reprice and relist daily.\nYou find out too late."),
        ("Search intent shifts", "Buyer keywords evolve with trends.\nManual SERP checks don't scale."),
        ("Social trend spikes", "TikTok, Reddit, Instagram drive demand.\nMost sellers miss the window."),
    ]
    for i, (title, body) in enumerate(problems):
        px = 0.38 + i * 3.12
        s.rect_f(px, 1.52, 2.88, 2.72, INK)
        s.rect_f(px, 1.52, 0.05, 2.72, COPPER)
        # Number oval (draw as tiny rect)
        s.rect_f(px + 0.22, 1.62, 0.28, 0.28, COPPER)
        s.text(str(i + 1), px + 0.27, 1.88, 9, SANS_B, CREAM)
        s.text(title, px + 0.22, 2.08, 14, SERIF_B, CREAM)
        for j, line in enumerate(body.split("\n")):
            s.text(line, px + 0.22, 2.45 + j * 0.28, 11, SANS, DKTEXT)

    # Bottom bar
    s.rect_f(0, 5.22, 10, 0.405, COPPDK)
    s.text("5.6M active Etsy sellers. Zero of them have an always-on market analyst.",
           5.0, 5.44, 11.5, SANS_B, CREAM, "center")


def slide_3(s: Slide):
    """Solution."""
    s.bg(CREAM)
    s.rule(SAGE, 4)
    s.section_label("THE SOLUTION", SAGE)
    s.headline("One shop URL. Seven agents.\nOnly actionable briefs.", 0.5, 0.75, 22)

    # Pipeline steps
    steps = ["Shop URL", "Bootstrap Profile", "SERP · Comp · Social", "Market Pulse", "Judge Agent", "Seller Brief"]
    colors = [INK, COPPDK, COPPDK, SOIL, SAGE, SAGE]
    total_w = 9.2
    sw = total_w / len(steps) - 0.12
    for i, (step, col) in enumerate(zip(steps, colors)):
        bx = 0.4 + i * (sw + 0.12)
        s.rect_f(bx, 1.55, sw, 0.72, col)
        s.text(step, bx + sw / 2, 1.98, 9.5, SANS_B, CREAM, "center")
        s.text(["one input", "Bright Data", "parallel", "normalized", "filtered", "actionable"][i],
               bx + sw / 2, 2.17, 8, SANS, DKTEXT if col != INK else HexColor("#C8A882"), "center")
        if i < len(steps) - 1:
            ax = bx + sw + 0.02
            s.rect_f(ax, 1.87, 0.08, 0.025, COPPER)  # tiny arrow

    # Callout
    s.rect_f(0.4, 2.5, 9.2, 0.65, DARK)
    s.rect_f(0.4, 2.5, 0.05, 0.65, GOLD)
    s.text("The Judge Agent filters 100% of signals.", 0.62, 2.75, 12, SANS_B, CREAM)
    s.text("Only those crossing the actionability threshold reach the seller.", 0.62, 2.98, 12, SANS, DKTEXT)

    # Two value props
    props = [
        ("✓  No credentials needed for demo — DEMO_MODE=true out of the box", SAGE),
        ("⚡  Live Bright Data path available — Web Unlocker + all tool abstractions", COPPER),
    ]
    for i, (prop, color) in enumerate(props):
        px = 0.4 + i * 4.7
        s.rect_f(px, 3.38, 4.45, 0.78, HexColor("#FEF6EC"))
        s.rect_f(px, 3.38, 0.05, 0.78, color)
        s.text(prop, px + 0.2, 3.72, 10, SANS, SOIL)

    s.text("Architecture: React/Vite → FastAPI → Scheduler → Agent Pipeline → Bright Data + LLM",
           5.0, 5.28, 9.5, SANS, MUTED, "center")


def slide_4(s: Slide):
    """Bright Data."""
    s.bg(INK)
    s.rule(COPPER, 4)
    s.section_label("BRIGHT DATA", COPPER)
    s.headline("Real web data powers every signal.", 0.5, 0.82, 26, CREAM, SERIF_B)

    # Tool grid 3x3
    tools = [
        "web_data_etsy_products", "search_engine", "scrape_as_markdown",
        "discover", "scrape_batch", "web_data_tiktok_posts",
        "web_data_reddit_posts", "web_data_instagram_reels", "web_data_google_shopping",
    ]
    for i, tool in enumerate(tools):
        col = i % 3
        row = i // 3
        tx = 0.42 + col * 3.08
        ty = 1.42 + row * 0.46
        s.rect_f(tx, ty, 2.9, 0.34, DARK)
        s.text(tool, tx + 0.14, ty + 0.23, 9.5, MONO, GOLD)

    # Mode boxes
    modes = [("Demo Mode", "Deterministic cached fixtures\n→ no credentials required", SAGE),
             ("Live Mode", "Bright Data Web Unlocker\n→ real markdown scraping", COPPER)]
    for i, (lbl, body, col) in enumerate(modes):
        mx = 0.42 + i * 4.7
        s.rect_f(mx, 3.2, 4.35, 1.1, DARK)
        s.rect_f(mx, 3.2, 0.05, 1.1, col)
        s.text(lbl, mx + 0.22, 3.48, 13, SANS_B, col)
        for j, line in enumerate(body.split("\n")):
            s.text(line, mx + 0.22, 3.75 + j * 0.26, 10.5, SANS, DKTEXT)

    s.text("Debug panel: tool name · latency · cache/live mode · redacted request shape",
           5.0, 5.28, 9.5, SANS, MUTED, "center")


def slide_5(s: Slide):
    """Agent Pipeline."""
    s.bg(CREAM)
    s.rule(COPPDK, 4)
    s.section_label("AGENT PIPELINE", COPPDK)
    s.headline("Seven typed agents. One actionable brief.", 0.5, 0.76, 22)

    # NIM callout top right
    s.rect_f(6.85, 0.42, 2.9, 0.6, DARK)
    s.text("NVIDIA NIM  ·  OpenRouter  ·  OpenClaw (optional)", 8.3, 0.75, 8.5, MONO, GOLD, "center")

    agents = [
        ("Shop Bootstrap", "Profiles listings, seed keywords, competitors", "etsy_products · scrape_markdown", COPPER),
        ("Keyword / SERP", "Tracks search intent and SERP position changes", "search_engine · discover", GOLD),
        ("Competitor Watch", "Monitors pricing, listings, and positioning", "etsy_products · scrape_batch", GOLD),
        ("Trend Scout", "Scans TikTok, Reddit, Instagram, Google Shopping", "tiktok · reddit · instagram · shopping", GOLD),
        ("Market Pulse", "Normalizes and deduplicates signals into market events", None, SOIL),
        ("Judge Agent", "Scores: actionability · urgency · confidence · novelty · evidence", None, SAGE),
        ("Brief Delivery", "Formats seller-ready action with evidence and why-now", None, COPPER),
    ]
    for i, (name, role, bd_tool, accent) in enumerate(agents):
        ay = 1.3 + i * 0.48
        s.rect_f(0.38, ay, 7.0, 0.4, INK)
        s.rect_f(0.38, ay, 0.04, 0.4, accent)
        # Number
        s.rect_f(0.52, ay + 0.08, 0.24, 0.24, accent)
        s.text(str(i + 1), 0.54, ay + 0.29, 8, SANS_B, CREAM)
        # Name
        s.text(name, 0.9, ay + 0.17, 12, SANS_B, CREAM)
        # Role
        s.text(role, 0.9, ay + 0.35, 9, SANS, DKTEXT)
        # BD tool
        if bd_tool:
            s.rect_f(5.02, ay + 0.08, 2.2, 0.24, DARK)
            s.text(bd_tool, 5.1, ay + 0.27, 8, MONO, GOLD)


def slide_6(s: Slide):
    """Demo Screenshots."""
    s.bg(PARCH)
    s.rule(COPPER, 4)
    s.section_label("LIVE DEMO", COPPER)
    s.headline("A dashboard that tells the story in 30 seconds.", 0.5, 0.76, 22)

    # Screenshot panels
    panels = [
        (SHOTS_DIR / "02-shop-bootstrap.png", "One URL. Instant shop intelligence profile.",
         "Shop profile · 7-agent metric strip · Workflow ribbon"),
        (SHOTS_DIR / "05-judge-brief.png", "Only actionable signals become briefs.",
         "Judge scores · Recommended actions · Evidence · Why-now"),
    ]
    for i, (path, caption, sub) in enumerate(panels):
        px = 0.38 + i * 4.92
        s.image(path, px, 1.3, 4.52, 2.85)
        # frame
        s.c.setStrokeColor(LINE)
        s.c.setLineWidth(1)
        s.c.rect(px * inch, PH - (1.3 + 2.85) * inch, 4.52 * inch, 2.85 * inch, fill=0, stroke=1)
        s.text(caption, px + 2.26, 4.32, 12, SANS_B, INK, "center")
        s.text(sub, px + 2.26, 4.58, 9.5, SANS, MUTED, "center")

    s.rect_f(0, 5.0, 10, 0.625, INK)
    s.text("Demo: etsypulse.vercel.app  ·  DEMO_MODE=true  ·  No credentials required  ·  48 tests passing",
           5.0, 5.3, 10.5, SANS, HexColor("#C8A882"), "center")


def slide_7(s: Slide):
    """Business Value."""
    s.bg(CREAM)
    s.rule(GOLD, 4)
    s.section_label("MARKET OPPORTUNITY", GOLD)
    s.headline("A $1.28B addressable market with proven willingness to pay.", 0.5, 0.76, 20)

    # Big stat cards
    stats = [("5.6M", "Active Etsy marketplace sellers", "Etsy 10-K, Dec 2025"),
             ("$876M", "Etsy services revenue 2025", "Sellers pay for growth tools")]
    for i, (num, lbl, sub) in enumerate(stats):
        sx = 0.38 + i * 4.85
        s.rect_f(sx, 1.3, 4.42, 1.26, INK)
        s.rect_f(sx, 1.3, 4.42, 0.04, GOLD)
        s.text(num, sx + 0.22, 2.1, 46, SERIF_B, GOLD)
        s.text(lbl, sx + 0.22, 2.35, 11, SANS_B, CREAM)
        s.text(sub, sx + 0.22, 2.53, 8.5, SANS, MUTED)

    # TAM/SAM box
    s.rect_f(0.38, 2.8, 4.42, 1.32, HexColor("#FEF6EC"))
    s.rect_f(0.38, 2.8, 0.05, 1.32, COPPER)
    s.text("TAM  →  $1.28B ARR", 0.58, 3.08, 14, SANS_B, INK)
    s.text("5.6M sellers × $19/month subscription", 0.58, 3.32, 10.5, SANS, SOIL)
    s.text("SAM  →  $191M–$319M ARR", 0.58, 3.62, 13, SANS_B, INK)
    s.text("15–25% of sellers already paying for growth tools", 0.58, 3.86, 10.5, SANS, SOIL)

    # Revenue tiers
    s.rect_f(5.0, 2.8, 4.62, 1.32, HexColor("#FEF6EC"))
    s.rect_f(5.0, 2.8, 0.05, 1.32, SAGE)
    tiers = [("Solo Seller", "$19–29/mo", "One shop, daily monitoring"),
             ("Power Seller", "$49–99/mo", "Multi-shop, live mode"),
             ("Agency", "$199+/mo", "Multiple shops, white-label")]
    for i, (tier, price, desc) in enumerate(tiers):
        ty = 3.02 + i * 0.38
        s.text(tier, 5.2, ty + 0.22, 10.5, SANS_B, INK)
        s.text(price, 6.85, ty + 0.22, 11.5, SANS_B, COPPER)
        s.text(desc, 7.85, ty + 0.22, 9, SANS, MUTED)

    s.rule(COPPDK, 3, 4.52 * inch + 4)
    s.text("eRank, Marmalead, EverBee give dashboards.  EtsyPulse gives decisions.",
           5.0, 4.6, 13, SERIF_B, COPPDK, "center")
    s.text("Source: Etsy Inc. Fourth Quarter and Full Year 2025 Results",
           5.0, 5.22, 8, SANS, MUTED, "center")


def slide_8(s: Slide):
    """Roadmap."""
    s.bg(INK)
    s.rule(COPPER, 4)
    s.section_label("ROADMAP", COPPER)
    s.headline("Built for the hackathon. Designed for production.", 0.5, 0.76, 24, CREAM, SERIF_B)

    cols = [
        ("NOW", SAGE, ["Live Vercel + Render deployment", "7-agent demo pipeline",
                       "Bright Data Web Unlocker live", "Judge Agent + NVIDIA NIM", "48 backend tests"]),
        ("NEAR TERM", GOLD, ["Live BD adapters for all tools", "Email / Slack notifications",
                             "Playwright demo test suite", "Seller brief feedback loop", "Seasonal opportunity packs"]),
        ("FUTURE", COPPER, ["Shopify, Amazon, Faire, Depop", "Multi-shop agency dashboard",
                            "Historical trend tracking", "OpenClaw agentToAgent", "SaaS subscription launch"]),
    ]
    for i, (label, col, items) in enumerate(cols):
        cx = 0.38 + i * 3.12
        # Header
        s.rect_f(cx, 1.38, 2.9, 0.38, col)
        s.text(label, cx + 1.45, 1.64, 11, SANS_B, INK, "center")
        # Items
        for j, item in enumerate(items):
            iy = 1.9 + j * 0.44
            s.rect_f(cx, iy, 2.9, 0.36, DARK)
            s.rect_f(cx, iy, 0.04, 0.36, col)
            s.text(item, cx + 0.18, iy + 0.24, 9.5, SANS, DKTEXT)

    # Closing statement
    s.rect_f(0.38, 4.66, 9.24, 0.4, DARK)
    s.text("EtsyPulse is the market intelligence layer small ecommerce sellers have always needed.",
           5.0, 4.93, 11.5, SERIF_B, CREAM, "center")

    s.text("GitHub: ZachDolph/etsypulse  ·  Demo: etsypulse.vercel.app  ·  Powered by Bright Data",
           5.0, 5.26, 9, SANS, MUTED, "center")


def main():
    OUT_MAIN.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(OUT_MAIN), pagesize=(PW, PH))

    slide_fns = [slide_1, slide_2, slide_3, slide_4, slide_5, slide_6, slide_7, slide_8]
    for i, fn in enumerate(slide_fns):
        fn(Slide(c))
        c.showPage()
        print(f"  Slide {i+1}/8 rendered")

    c.save()
    import shutil
    shutil.copy(str(OUT_MAIN), str(OUT_FINAL))
    print(f"\n✓ PDF saved → {OUT_MAIN}")
    print(f"✓ Copied  → {OUT_FINAL}")


if __name__ == "__main__":
    main()
