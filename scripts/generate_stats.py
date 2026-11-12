"""Builds assets/github-stats.svg from the public contribution calendar.
Run from the repo root:  python3 scripts/generate_stats.py [username]
Uses only the standard library so it can run in a GitHub Action without installs."""
import re
import sys
import urllib.request
from datetime import date, timedelta
from pathlib import Path
from svgkit import W, CARD, BORDER, TEXT, MUTED, github_logo, icon, text, svg

USER = sys.argv[1] if len(sys.argv) > 1 else "tanaygit0530"
OUT = Path(__file__).resolve().parent.parent / "assets" / "github-stats.svg"
LEVEL_FILL = ["#1b222c", "#0e4429", "#006d32", "#26a641", "#39d353"]


def fetch():
    req = urllib.request.Request(f"https://github.com/users/{USER}/contributions",
                                 headers={"User-Agent": "profile-readme-stats"})
    html = urllib.request.urlopen(req, timeout=30).read().decode()

    tips = {}
    for m in re.finditer(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', html):
        n = re.match(r"\s*(\d+)\s+contribution", m.group(2))
        tips[m.group(1)] = int(n.group(1)) if n else 0

    days = {}  # date -> (week, dow, level, count)
    for m in re.finditer(r"<td[^>]*ContributionCalendar-day[^>]*>", html):
        td = m.group(0)
        d = re.search(r'data-date="([\d-]+)"', td)
        i = re.search(r'id="contribution-day-component-(\d+)-(\d+)"', td)
        lv = re.search(r'data-level="(\d)"', td)
        if not (d and i and lv):
            continue
        dow, week = int(i.group(1)), int(i.group(2))
        days[date.fromisoformat(d.group(1))] = (week, dow, int(lv.group(1)), tips.get(i.group(0)[4:-1], 0))

    total = re.search(r"([\d,]+)\s+contributions?\s+in the last year", html)
    total = int(total.group(1).replace(",", "")) if total else sum(v[3] for v in days.values())
    if not days:
        raise SystemExit("could not parse the contribution calendar")
    return days, total


def streaks(days):
    ordered = sorted(days)
    longest = run = 0
    for d in ordered:
        run = run + 1 if days[d][3] > 0 else 0
        longest = max(longest, run)
    current, d = 0, ordered[-1]
    if days[d][3] == 0:          # today not counted yet -> streak may still be alive from yesterday
        d -= timedelta(days=1)
    while d in days and days[d][3] > 0:
        current += 1
        d -= timedelta(days=1)
    return current, longest


H = 240                       # banner height; both cards are H-10 tall
EMPTY = LEVEL_FILL[0]


def r(v):
    return f"{v:.4f}".rstrip("0").rstrip(".")


def anim(attr, values, times, T, discrete=False):
    mode = ' calcMode="discrete"' if discrete else ""
    return (f'<animate attributeName="{attr}" values="{";".join(map(str, values))}" '
            f'keyTimes="{";".join(r(t) for t in times)}" dur="{T:.1f}s" repeatCount="indefinite"{mode}/>')


def stars(x0, y0, w, h, n=46, seed=7):
    import random
    rnd = random.Random(seed)
    out = ""
    for _ in range(n):
        x, y = x0 + rnd.random() * w, y0 + rnd.random() * h
        rad, dur, beg = rnd.choice((0.6, 0.8, 1.1)), rnd.uniform(1.5, 4), rnd.uniform(0, 3)
        out += (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rad}" fill="#c9d1d9">'
                f'<animate attributeName="opacity" values="0.15;0.9;0.15" dur="{dur:.1f}s" '
                f'begin="-{beg:.1f}s" repeatCount="indefinite"/></circle>')
    return out


def shooter(days, total):
    """Contribution calendar as a looping space-shooter: a ship sweeps left to right
    under the grid, shoots every active day, the square flashes and explodes, and the
    whole grid fades back in before the loop restarts. Pure SMIL so it plays inside <img>."""
    cx0, cw = 602, 566
    out = f'<rect x="{cx0}" y="4" width="{cw}" height="{H - 10}" rx="12" fill="{CARD}" stroke="{BORDER}" stroke-width="1.5"/>'
    out += f'<clipPath id="card"><rect x="{cx0}" y="4" width="{cw}" height="{H - 10}" rx="12"/></clipPath><g clip-path="url(#card)">'
    out += stars(cx0 + 6, 10, cw - 12, H - 24)
    out += text(620, 34, f"{total:,} contributions in the last year", 16, TEXT)

    gx, gy, pitch, cell = 650, 74, 9.6, 8
    weeks = max(v[0] for v in days.values()) + 1
    if weeks > 53:
        pitch = 505 / weeks
    ship_y = 205

    targets = sorted((v[0], -v[1], d) for d, v in days.items() if v[2] > 0)  # by column, bottom row first
    n = max(1, len(targets))
    step = 0.16 if n > 120 else 0.25
    lead, travel, reset = 1.0, 0.22, 2.2
    T = lead + n * step + travel + reset
    fire = {t[2]: lead + i * step for i, t in enumerate(targets)}
    restore = (T - reset * 0.6) / T

    grid = fx = ""
    last_month, last_x = None, -99
    for d in sorted(days):
        week, dow, level, _ = days[d]
        x, y = gx + week * pitch, gy + dow * pitch
        if level == 0:
            grid += f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="1.5" fill="{EMPTY}" stroke="#262d38" stroke-width="0.8"/>'
        else:
            f = fire[d] / T
            h = (fire[d] + travel) / T
            c = LEVEL_FILL[level]
            grid += (f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="1.5" fill="{c}">'
                     + anim("fill", [c, c, "#fde047", "#f97316", EMPTY, EMPTY, c],
                            [0, h, h + 0.002, h + 0.008, h + 0.016, restore, 1], T) + "</rect>")
            bx = x + cell / 2 - 1
            # bullet
            fx += (f'<rect x="{bx:.1f}" y="{ship_y - 12}" width="2" height="7" rx="1" fill="#facc15" opacity="0">'
                   + anim("y", [ship_y - 12, ship_y - 12, y, y], [0, f, h, 1], T)
                   + anim("opacity", [0, 1, 0], [0, f, h], T, discrete=True) + "</rect>")
            # explosion burst
            ex, ey = x + cell / 2, y + cell / 2
            e2 = min(h + 0.02, 0.999)
            fx += (f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="0" fill="none" stroke="#f59e0b" stroke-width="2" opacity="0">'
                   + anim("r", [0, 0, 9, 9], [0, h, e2, 1], T)
                   + anim("opacity", [0, 0, 1, 0, 0], [0, h, h + 0.001, e2, 1], T) + "</circle>")
        if d.day <= 7 and d.month != last_month and x - last_x > 26 and x < 1140:
            out += text(f"{x:.0f}", 64, d.strftime("%b"), 11.5, MUTED)
            last_month, last_x = d.month, x
    for label, dow in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
        out += text(617, gy + dow * pitch + 8, label, 11, MUTED)

    # ship: arrives under each target's column right as it fires, then glides home during the reset
    xs = [gx + 4] + [gx + t[0] * pitch + cell / 2 for t in targets] + [gx + 4]
    ts = [0] + [fire[t[2]] / T for t in targets] + [1]
    ship = (f'<g><animateTransform attributeName="transform" type="translate" '
            f'values="{";".join(f"{x:.1f} {ship_y}" for x in xs)}" keyTimes="{";".join(r(t) for t in ts)}" '
            f'dur="{T:.1f}s" repeatCount="indefinite"/>'
            '<path d="M0 -9 L3 -2 L8 2 L8 5 L3 3 L2 6 L-2 6 L-3 3 L-8 5 L-8 2 L-3 -2 Z" fill="#60a5fa"/>'
            '<rect x="-1" y="-6" width="2" height="4" fill="#bfdbfe"/>'
            '<path d="M-2 6 L0 10 L2 6 Z" fill="#f97316"><animate attributeName="opacity" values="1;0.3;1" dur="0.25s" repeatCount="indefinite"/></path>'
            '</g>')
    return out + grid + fx + ship + "</g>"


def build(days, total):
    current, longest = streaks(days)
    # ---- left card: totals + streaks (content drawn for a 176px card, shifted to centre)
    left = f'<rect x="33" y="4" width="550" height="{H - 10}" rx="12" fill="{CARD}" stroke="{BORDER}" stroke-width="1.5"/>'
    s = github_logo(121, 44, 38)
    s += text(140, 113, "Total Contributions", 16, MUTED, anchor="middle")
    s += text(140, 150, f"{total:,}", 30, TEXT, 700, anchor="middle")
    for x in (243, 418):
        s += f'<line x1="{x}" y1="48" x2="{x}" y2="146" stroke="{BORDER}" stroke-width="1.5"/>'
    # ring with a gap at the top for the flame
    s += (f'<circle cx="331" cy="80" r="37" fill="none" stroke="{TEXT}" stroke-width="3" '
          f'stroke-dasharray="200 32.5" stroke-dashoffset="-16" transform="rotate(-90 331 80)"/>')
    s += icon("flame", 322, 34, 18, TEXT, 2)
    s += text(331, 91, str(current), 28, TEXT, 700, anchor="middle")
    s += text(331, 145, "Current Streak", 16, MUTED, anchor="middle")
    s += text(501, 92, str(longest), 38, TEXT, 700, anchor="middle")
    s += text(501, 126, "Longest Streak", 16, MUTED, anchor="middle")
    left += f'<g transform="translate(0 {(H - 186) / 2:.0f})">{s}</g>'

    OUT.write_text(svg(W, H, left + shooter(days, total), f"GitHub stats for {USER}"), encoding="utf-8")
    print(f"wrote {OUT.name}: total={total} current={current} longest={longest}")


if __name__ == "__main__":
    build(*fetch())
