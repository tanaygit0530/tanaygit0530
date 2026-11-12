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


def build(days, total):
    current, longest = streaks(days)
    # ---- left card: totals + streaks
    left = f'<rect x="33" y="4" width="550" height="176" rx="12" fill="{CARD}" stroke="{BORDER}" stroke-width="1.5"/>'
    left += github_logo(121, 44, 38)
    left += text(140, 113, "Total Contributions", 16, MUTED, anchor="middle")
    left += text(140, 150, f"{total:,}", 30, TEXT, 700, anchor="middle")
    for x in (243, 418):
        left += f'<line x1="{x}" y1="48" x2="{x}" y2="146" stroke="{BORDER}" stroke-width="1.5"/>'
    # ring with a gap at the top for the flame
    left += (f'<circle cx="331" cy="80" r="37" fill="none" stroke="{TEXT}" stroke-width="3" '
             f'stroke-dasharray="200 32.5" stroke-dashoffset="-16" transform="rotate(-90 331 80)"/>')
    left += icon("flame", 322, 34, 18, TEXT, 2)
    left += text(331, 91, str(current), 28, TEXT, 700, anchor="middle")
    left += text(331, 145, "Current Streak", 16, MUTED, anchor="middle")
    left += text(501, 92, str(longest), 38, TEXT, 700, anchor="middle")
    left += text(501, 126, "Longest Streak", 16, MUTED, anchor="middle")

    # ---- right card: contribution calendar
    right = f'<rect x="602" y="4" width="566" height="176" rx="12" fill="{CARD}" stroke="{BORDER}" stroke-width="1.5"/>'
    right += text(620, 36, f"{total:,} contributions in the last year", 16, TEXT)
    gx, gy, pitch, cell = 654, 80, 9.6, 8
    weeks = max(v[0] for v in days.values()) + 1
    if weeks > 53:
        pitch = 505 / weeks
    last_month, last_x = None, -99
    for d in sorted(days):
        week, dow, level, _ = days[d]
        x, y = gx + week * pitch, gy + dow * pitch
        stroke = f' stroke="#262d38" stroke-width="0.8"' if level == 0 else ""
        right += f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="1.5" fill="{LEVEL_FILL[level]}"{stroke}/>'
        if d.day <= 7 and d.month != last_month and x - last_x > 26 and x < 1140:
            right += text(f"{x:.0f}", 68, d.strftime("%b"), 11.5, MUTED)
            last_month, last_x = d.month, x
    for label, dow in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
        right += text(619, gy + dow * pitch + 8, label, 11, MUTED)

    OUT.write_text(svg(W, 186, left + right, f"GitHub stats for {USER}"), encoding="utf-8")
    print(f"wrote {OUT.name}: total={total} current={current} longest={longest}")


if __name__ == "__main__":
    build(*fetch())
