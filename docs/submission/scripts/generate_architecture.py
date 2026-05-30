"""Generate the EtsyPulse architecture diagram."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT_MAIN = Path("docs/submission/architecture-diagram.png")
OUT_FINAL = Path("docs/submission/final/architecture-diagram.png")
W, H = 1800, 830

# ── Palette (matches app warm-brown aesthetic) ───────────────────────────────
BG        = "#f6e8d0"
GRID      = "#e8d4b8"
INK       = "#21160f"
SOIL      = "#5b3b27"
MUTED     = "#907060"
PAPER     = "#fff7ea"
COPPER    = "#b4572d"
COPPER_DK = "#78361e"
SAGE      = "#6f8663"
GOLD      = "#d59a38"
BLUE      = "#264f69"
DARK_CARD = "#21160f"
DARK_TEXT = "#ffe1b7"
GOLD_TEXT = "#e9bd75"
SLATE     = "#3a4a5a"


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = []
    if bold:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def rr(draw: ImageDraw.ImageDraw, xy, fill, outline=None, width=3, radius=20):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def centered(draw: ImageDraw.ImageDraw, box, text: str, fill, size=22, bold=False):
    f = _font(size, bold)
    bbox = draw.multiline_textbbox((0, 0), text, font=f, spacing=5, align="center")
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    bx = box[0] + (box[2] - box[0] - tw) / 2
    by = box[1] + (box[3] - box[1] - th) / 2
    draw.multiline_text((bx, by), text, font=f, fill=fill, spacing=5, align="center")


def h_arrow(draw: ImageDraw.ImageDraw, x0, y, x1, color=SOIL, width=4):
    draw.line([(x0, y), (x1, y)], fill=color, width=width)
    draw.polygon([(x1, y), (x1 - 14, y - 8), (x1 - 14, y + 8)], fill=color)


def v_arrow(draw: ImageDraw.ImageDraw, x, y0, y1, color=SOIL, width=4):
    draw.line([(x, y0), (x, y1)], fill=color, width=width)
    draw.polygon([(x, y1), (x - 8, y1 - 14), (x + 8, y1 - 14)], fill=color)


def diag_arrow(draw: ImageDraw.ImageDraw, start, end, color=SOIL, width=3):
    draw.line([start, end], fill=color, width=width)
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = (dx**2 + dy**2) ** 0.5
    ux, uy = dx / length, dy / length
    p1 = (end[0] - 14 * ux + 8 * uy, end[1] - 14 * uy - 8 * ux)
    p2 = (end[0] - 14 * ux - 8 * uy, end[1] - 14 * uy + 8 * ux)
    draw.polygon([end, p1, p2], fill=color)


def label_pill(draw: ImageDraw.ImageDraw, cx, cy, text, bg, fg, size=17):
    f = _font(size, False)
    bbox = draw.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 10, 6
    x0, y0 = cx - tw // 2 - pad_x, cy - th // 2 - pad_y
    x1, y1 = cx + tw // 2 + pad_x, cy + th // 2 + pad_y
    draw.rounded_rectangle([x0, y0, x1, y1], radius=12, fill=bg)
    draw.text((x0 + pad_x, y0 + pad_y), text, font=f, fill=fg)


def main() -> None:
    OUT_MAIN.parent.mkdir(parents=True, exist_ok=True)
    OUT_FINAL.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Grid background
    for i in range(0, W, 36):
        draw.line([(i, 0), (i, H)], fill=GRID, width=1)
    for i in range(0, H, 36):
        draw.line([(0, i), (W, i)], fill=GRID, width=1)

    # ── Title ─────────────────────────────────────────────────────────────────
    draw.text((60, 44), "EtsyPulse Architecture", fill=INK, font=_font(54, True))
    draw.text((62, 112), "Set shop once  →  agents monitor  →  Judge filters noise  →  seller gets a brief",
              fill=SOIL, font=_font(26))

    # ── Row 1: Infrastructure layer ───────────────────────────────────────────
    row1_y = 175
    infra = [
        (60,  row1_y, 310, row1_y + 120, "React / Vite\nDashboard",  PAPER,  INK,  COPPER_DK),
        (370, row1_y, 620, row1_y + 120, "FastAPI\nBackend",         COPPER_DK, PAPER, COPPER_DK),
        (680, row1_y, 930, row1_y + 120, "Scheduler +\nRate Limiter", PAPER, INK,  COPPER_DK),
        (990, row1_y, 1240, row1_y + 120, "SQLite /\nPostgres",       PAPER, INK,  COPPER_DK),
    ]
    for x0, y0, x1, y1, label, bg, fg, outline in infra:
        rr(draw, (x0, y0, x1, y1), bg, outline, 4, 22)
        centered(draw, (x0, y0, x1, y1), label, fg, 26, True)
    # arrows between infra boxes
    for sx in [310, 620, 930]:
        h_arrow(draw, sx + 5, row1_y + 60, sx + 55)

    # ── OpenClaw optional layer ───────────────────────────────────────────────
    oc_x0, oc_y0, oc_x1, oc_y1 = 1310, row1_y, 1730, row1_y + 120
    rr(draw, (oc_x0, oc_y0, oc_x1, oc_y1), PAPER, BLUE, 3, 22)
    centered(draw, (oc_x0, oc_y0, oc_x1, oc_y1), "OpenClaw\n(optional coordination)", BLUE, 24, True)
    # dashed connection from Backend to OpenClaw
    for xi in range(1245, 1305, 16):
        draw.line([(xi, row1_y + 60), (xi + 8, row1_y + 60)], fill=BLUE, width=3)
    draw.polygon([(1310, row1_y + 60), (1296, row1_y + 52), (1296, row1_y + 68)], fill=BLUE)
    draw.text((1252, row1_y + 64), "optional", fill=BLUE, font=_font(17))

    # ── Section label for agent pipeline ─────────────────────────────────────
    pipe_top = 340
    draw.text((60, pipe_top - 30), "Typed Agent Pipeline", fill=MUTED, font=_font(20, True))

    # ── Agent pipeline dark card ──────────────────────────────────────────────
    PIPE_L, PIPE_R = 60, 1050
    agent_rows = [
        # row, agents: (label, has_bd, bd_tools, color_accent)
        [
            ("Shop Bootstrap", True,  ["etsy_products", "scrape_markdown"],  COPPER),
        ],
        [
            ("Keyword / SERP", True,  ["search_engine", "discover"],          GOLD),
            ("Competitor Watch", True, ["etsy_products", "scrape_batch"],      GOLD),
            ("Trend Scout", True,     ["tiktok_posts", "reddit_posts",
                                       "instagram_reels", "google_shopping"],  GOLD),
        ],
        [
            ("Market Pulse", False, [], SAGE),
        ],
        [
            ("Judge Agent", False, [], SAGE),
        ],
        [
            ("Brief Delivery", False, [], COPPER),
        ],
    ]

    # Calculate layout
    ROW_H = 64
    ROW_GAP = 14
    PIPE_PAD_X = 28
    PIPE_PAD_TOP = 28

    # Compute total height of pipeline card
    n_rows = len(agent_rows)
    card_h = PIPE_PAD_TOP * 2 + n_rows * ROW_H + (n_rows - 1) * ROW_GAP
    card_y0 = pipe_top
    card_y1 = card_y0 + card_h

    rr(draw, (PIPE_L, card_y0, PIPE_R, card_y1), DARK_CARD, DARK_CARD, 4, 32)

    # Draw each agent row
    row_centers = []
    for ri, row_agents in enumerate(agent_rows):
        row_y = card_y0 + PIPE_PAD_TOP + ri * (ROW_H + ROW_GAP)
        n = len(row_agents)
        avail_w = PIPE_R - PIPE_L - 2 * PIPE_PAD_X
        agent_w = min(220, (avail_w - (n - 1) * 14) // n)
        total_w = n * agent_w + (n - 1) * 14
        start_x = PIPE_L + PIPE_PAD_X + (avail_w - total_w) // 2
        centers_this_row = []
        for ai, (label, has_bd, _, accent) in enumerate(row_agents):
            ax0 = start_x + ai * (agent_w + 14)
            ax1 = ax0 + agent_w
            ay0, ay1 = row_y, row_y + ROW_H
            rr(draw, (ax0, ay0, ax1, ay1), "#2e1f12", accent, 2, 18)
            centered(draw, (ax0, ay0, ax1, ay1), label, PAPER, 20, True)
            cx = (ax0 + ax1) // 2
            cy = (ay0 + ay1) // 2
            centers_this_row.append((cx, cy, ax0, ay0, ax1, ay1, has_bd))
        row_centers.append((row_y, row_y + ROW_H, centers_this_row))

    # Vertical flow arrows between pipeline rows
    for ri in range(len(row_centers) - 1):
        _, bot_y, this_row = row_centers[ri]
        next_top, _, next_row = row_centers[ri + 1]
        # Arrow from center-bottom of each agent to center-top of next row
        if len(this_row) == 1 and len(next_row) == 1:
            cx = this_row[0][0]
            v_arrow(draw, cx, bot_y + 2, next_top - 2, GOLD_TEXT, 3)
        elif len(this_row) > 1 and len(next_row) == 1:
            # Fan-in: all current agents → single next agent
            mid_y = (bot_y + next_top) // 2
            for cx, cy, *_ in this_row:
                draw.line([(cx, bot_y + 2), (cx, mid_y)], fill=GOLD_TEXT, width=2)
            next_cx = next_row[0][0]
            min_cx = min(c[0] for c in this_row)
            max_cx = max(c[0] for c in this_row)
            draw.line([(min_cx, mid_y), (max_cx, mid_y)], fill=GOLD_TEXT, width=2)
            draw.line([(next_cx, mid_y), (next_cx, next_top - 2)], fill=GOLD_TEXT, width=2)
            draw.polygon([(next_cx, next_top - 2), (next_cx - 7, next_top - 14), (next_cx + 7, next_top - 14)], fill=GOLD_TEXT)
        elif len(this_row) == 1 and len(next_row) > 1:
            # Fan-out: single → multiple
            mid_y = (bot_y + next_top) // 2
            src_cx = this_row[0][0]
            draw.line([(src_cx, bot_y + 2), (src_cx, mid_y)], fill=GOLD_TEXT, width=2)
            min_cx = min(c[0] for c in next_row)
            max_cx = max(c[0] for c in next_row)
            draw.line([(min_cx, mid_y), (max_cx, mid_y)], fill=GOLD_TEXT, width=2)
            for cx, cy, *_ in next_row:
                draw.line([(cx, mid_y), (cx, next_top - 2)], fill=GOLD_TEXT, width=2)
                draw.polygon([(cx, next_top - 2), (cx - 7, next_top - 14), (cx + 7, next_top - 14)], fill=GOLD_TEXT)

    # ── Right-side data provider boxes ────────────────────────────────────────
    # Leave a 60px gap to the right of PIPE_R for the connecting arrows
    PROV_L = PIPE_R + 60
    PROV_R = W - 40
    PROV_GAP = 16
    BD_h = int(card_h * 0.57)
    BD_y0, BD_y1 = card_y0, card_y0 + BD_h
    LLM_y0, LLM_y1 = BD_y1 + PROV_GAP, card_y1

    rr(draw, (PROV_L, BD_y0, PROV_R, BD_y1), PAPER, COPPER, 4, 24)
    rr(draw, (PROV_L, LLM_y0, PROV_R, LLM_y1), PAPER, SAGE, 4, 24)

    # Bright Data box content
    TXT_L = PROV_L + 28
    draw.text((TXT_L, BD_y0 + 18), "Bright Data", fill=COPPER_DK, font=_font(28, True))
    # Subtle "used by" sub-label
    draw.text((TXT_L, BD_y0 + 52), "Bootstrap · Keyword/SERP · Competitor · Trend agents", fill=COPPER, font=_font(16))
    bd_tools = [
        "web_data_etsy_products   ·   scrape_as_markdown",
        "search_engine  ·  discover  ·  scrape_batch",
        "web_data_tiktok_posts  ·  web_data_reddit_posts",
        "web_data_instagram_reels  ·  web_data_google_shopping",
        "Web Unlocker  (live markdown path)",
    ]
    ty = BD_y0 + 78
    for line in bd_tools:
        draw.text((TXT_L, ty), line, fill=SOIL, font=_font(19))
        ty += 30

    # LLM box content
    draw.text((TXT_L, LLM_y0 + 16), "LLM Providers", fill="#2d5242", font=_font(26, True))
    draw.text((TXT_L, LLM_y0 + 48), "Judge Agent only", fill=SAGE, font=_font(16))
    llm_lines = [
        "NVIDIA NIM  (primary)",
        "OpenRouter free-router  (fallback)",
        "Test stub  (demo / CI mode)",
    ]
    ty = LLM_y0 + 72
    for line in llm_lines:
        draw.text((TXT_L, ty), line, fill=SOIL, font=_font(20))
        ty += 33

    # Connection arrows: clean horizontal lines from PIPE_R → PROV_L
    bd_entry_y = (BD_y0 + BD_y1) // 2
    llm_entry_y = (LLM_y0 + LLM_y1) // 2
    h_arrow(draw, PIPE_R + 5, bd_entry_y, PROV_L - 5, COPPER, 4)

    # LLM: elbow from Judge Agent row
    judge_row_idx = 3
    judge_row = row_centers[judge_row_idx]
    judge_y = (judge_row[0] + judge_row[1]) // 2
    elbow_x = PIPE_R + 30
    draw.line([(PIPE_R + 5, judge_y), (elbow_x, judge_y)], fill=SAGE, width=3)
    draw.line([(elbow_x, judge_y), (elbow_x, llm_entry_y)], fill=SAGE, width=3)
    h_arrow(draw, elbow_x, llm_entry_y, PROV_L - 5, SAGE, 3)

    # ── Footer ────────────────────────────────────────────────────────────────
    foot_y = card_y1 + 22
    draw.text((60, foot_y),
              "Demo mode: cached Bright Data fixtures + deterministic LLM stubs — no credentials required.",
              fill=MUTED, font=_font(22))
    draw.text((60, foot_y + 32),
              "Live mode: Web Unlocker path active for scrape_markdown; structured product adapters use cache fallback until wired.",
              fill=MUTED, font=_font(20))

    img.save(str(OUT_MAIN), "PNG")
    import shutil
    shutil.copy(str(OUT_MAIN), str(OUT_FINAL))
    print(f"Saved → {OUT_MAIN}")


if __name__ == "__main__":
    main()
