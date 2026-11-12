"""Builds every static SVG used by README.md into assets/.
Run from the repo root:  python3 scripts/build_static.py
(The GitHub stats card is built separately by generate_stats.py.)"""
import re
from pathlib import Path
from xml.sax.saxutils import escape
from svgkit import W, CARD, BORDER, TEXT, MUTED, ACCENT, icon, github_logo, text, svg

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SRC_ICONS = Path(__file__).resolve().parent / "icons"
ASSETS.mkdir(exist_ok=True)


def write(name, content):
    (ASSETS / name).write_text(content, encoding="utf-8")
    print("wrote", name)


# ---------------------------------------------------------------- header
def header():
    lines = (ASSETS / "portrait.txt").read_text().rstrip("\n").split("\n")
    cols = max(len(l) for l in lines)
    px_w, top, bottom = 345, 34, 336           # portrait box
    lh = (bottom - top) / len(lines)
    fs = lh * 0.98
    art = []
    for i, l in enumerate(lines):
        l = l.ljust(cols)
        art.append(f'<text x="58" y="{top + (i + 1) * lh:.2f}" textLength="{px_w}" lengthAdjust="spacing" '
                   f'xml:space="preserve">{escape(l)}</text>')
    art = (f'<g font-family="Menlo, Consolas, \'DejaVu Sans Mono\', \'Courier New\', monospace" '
           f'font-size="{fs:.2f}" fill="#e6e8ee">{"".join(art)}</g>')

    rows = [("cap", "Third-Year B.Tech IT Student   |   CGPA: 9.03/10"),
            ("building", "Jr Technical Officer @ ISTE-VESIT (2026 – Present)"),
            ("code", "Full-Stack Developer   |   Hackathon Enthusiast"),
            ("pin", "Mumbai, India")]
    info = ""
    for i, (ic, label) in enumerate(rows):
        y = 192 + i * 37
        info += icon(ic, 474, y - 20, 26) + text(526, y, label, 19, MUTED, extra='xml:space="preserve"')

    body = (art
            + f'<line x1="416" y1="50" x2="416" y2="320" stroke="{BORDER}" stroke-width="1.5"/>'
            + text(466, 100, "Tanay Patil", 56, TEXT, 800, extra='letter-spacing="-0.5"')
            + f'<rect x="766" y="93" width="34" height="5" rx="1" fill="{ACCENT}">'
              f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" repeatCount="indefinite"/></rect>'
            + text(473, 143, "B.Tech IT (Third Year) @ VESIT, Mumbai", 24, MUTED)
            + info)
    write("header.svg", svg(W, 350, body, "Tanay Patil – B.Tech IT @ VESIT, Mumbai"))


# ---------------------------------------------------------------- section titles
def bar_icon(x, y):
    # stepped bar chart like the reference
    bars = [(0, 18, 4), (6, 12, 4), (12, 6, 4), (18, 0, 4), (24, 0, 0)]
    out = "".join(f'<rect x="{x + bx}" y="{y + by}" width="{w}" height="{24 - by}" rx="1" fill="{TEXT}"/>'
                  for bx, by, w in bars if w)
    return out + f'<rect x="{x}" y="{y + 26}" width="24" height="2" fill="{TEXT}"/>'


def section(fname, ic, title, char_w=14.4):
    ico = bar_icon(38, 20) if ic == "bars" else icon(ic, 36, 18, 34, ACCENT if ic == "link" else TEXT, 1.7)
    tx = 92
    line_x = tx + len(title) * char_w + 24
    body = (ico + text(tx, 46, title, 27, TEXT, 600)
            + f'<line x1="{line_x:.0f}" y1="37" x2="1164" y2="37" stroke="#3d444d" stroke-width="1.5"/>')
    write(fname, svg(W, 70, body, title))


# ---------------------------------------------------------------- connect buttons
def button(fname, w, inner, title):
    body = (f'<rect x="1" y="1" width="{w - 2}" height="58" rx="11" fill="{CARD}" stroke="#3d444d" stroke-width="1.5"/>'
            + inner)
    write(fname, svg(w, 60, body, title, bg=False))


def buttons():
    button("btn-github.svg", 92, github_logo(28, 12, 36), "GitHub")
    button("btn-linkedin.svg", 92,
           f'<rect x="28" y="12" width="36" height="36" rx="5" fill="#0a66c2"/>'
           f'<text x="46.5" y="43" font-family="Helvetica, Arial, sans-serif" font-size="31" font-weight="700" '
           f'fill="#fff" text-anchor="middle" letter-spacing="-1">in</text>', "LinkedIn")
    # Gmail "M": blue + green legs, red V, yellow/dark-red corners
    gm = ('<g transform="translate(26 16)">'
          '<path d="M0 6v22h9V13z" fill="#4285f4"/>'
          '<path d="M31 13v15h9V6z" fill="#34a853"/>'
          '<path d="M31 2 20 10.5 9 2v11l11 8.5L31 13z" fill="#ea4335"/>'
          '<path d="M31 2v11l9-7V3c0-3-3.5-4.8-6-3z" fill="#fbbc04"/>'
          '<path d="M0 3v3l9 7V2L6 0C3.5-1.8 0 0 0 3z" fill="#c5221f"/></g>')
    button("btn-gmail.svg", 92, gm, "Gmail")
    button("btn-portfolio.svg", 198,
           icon("link", 20, 17, 26, TEXT, 1.8) + text(68, 37, "Portfolio", 19, TEXT, 500)
           + icon("external", 152, 19, 22, TEXT, 1.8), "Portfolio")


# ---------------------------------------------------------------- tech stack
def embed(name, x, y, size, prefix):
    raw = (SRC_ICONS / f"{name}.svg").read_text()
    raw = re.sub(r"<\?xml[^>]*\?>", "", raw).strip()
    raw = re.sub(r'id="([^"]+)"', rf'id="{prefix}\1"', raw)
    raw = raw.replace("url(#", f"url(#{prefix}").replace('href="#', f'href="#{prefix}')
    return re.sub(r'<svg width="48" height="48"', f'<svg x="{x}" y="{y}" width="{size}" height="{size}"', raw, count=1)


def tech_stack():
    row1 = ["java", "python", "js", "ts", "react", "nextjs", "nodejs", "express", "mongodb",
            "firebase", "supabase", "postgres", "docker", "aws", "git"]
    row2 = ["tailwind", "bootstrap", "html", "css", "vite", "CLOUDINARY", "figma", "vscode", "github"]
    size, pitch, x0 = 64, 76.4, 36
    cloud_path = re.search(r' d="([^"]+)"', (SRC_ICONS / "si-cloudinary.svg").read_text()).group(1)
    out = ""
    for r, row in enumerate([row1, row2]):
        for i, name in enumerate(row):
            x, y = x0 + i * pitch, 8 + r * 78
            if name == "CLOUDINARY":
                out += (f'<rect x="{x:.1f}" y="{y}" width="{size}" height="{size}" rx="15" fill="#242938"/>'
                        f'<path transform="translate({x + 12:.1f} {y + 12}) scale(1.6667)" fill="#3e8ef7" d="{cloud_path}"/>')
            else:
                out += embed(name, round(x, 1), y, size, f"i{r}{i}_")
    write("tech-stack.svg", svg(W, 158, out, "Tech stack"))


# ---------------------------------------------------------------- about card
def about():
    rows = [("rocket", "I love building real-world products that solve practical problems."),
            ("layers", "Interested in Full-Stack Development, DSA, DBMS, and AI Systems (RAG, OCR)."),
            ("trophy", "1st Runner-Up @ SYRUS 7.0   |   2nd Runner-Up @ Genesis 2.0"),
            ("mountain", "Outside tech, I enjoy travelling, trekking, and riding.")]
    body = f'<rect x="33" y="6" width="1134" height="202" rx="14" fill="{CARD}" stroke="{BORDER}" stroke-width="1.5"/>'
    for i, (ic, label) in enumerate(rows):
        y = 50 + i * 43.5
        body += icon(ic, 66, y - 20, 28, ACCENT, 1.7) + text(117, y, label, 19, MUTED, extra='xml:space="preserve"')

    stroke = 'fill="none" stroke="#9aa3b5" stroke-linejoin="round" stroke-linecap="round"'
    ridge = "772,192 850,150 880,160 930,118 962,92 990,120 1018,100 1062,140 1100,160 1150,190"
    art = (f'<circle cx="958" cy="64" r="31" fill="none" stroke="{ACCENT}" stroke-width="1.8"/>'
           f'<polygon points="{ridge} 1150,200 772,200" fill="{CARD}"/>'
           f'<polyline points="{ridge}" {stroke} stroke-width="1.6"/>'
           f'<polyline points="962,92 950,128 930,150 912,175" {stroke} stroke-width="1"/>'
           f'<polyline points="1018,100 1008,130 990,155" {stroke} stroke-width="1"/>'
           f'<polyline points="880,160 905,168 935,165 960,178 1000,172 1040,182" {stroke} stroke-width="1"/>'
           f'<line x1="772" y1="192" x2="1150" y2="192" stroke="#4a5262" stroke-width="1"/>')

    def tree(x, base, h):
        w = h * 0.36
        return (f'<polygon points="{x},{base - h} {x + w},{base - h * .45} {x + w * .55},{base - h * .45} '
                f'{x + w * 1.2},{base - 2} {x - w * 1.2},{base - 2} {x - w * .55},{base - h * .45} {x - w},{base - h * .45}" '
                f'fill="#6e7681"/><rect x="{x - 1.5}" y="{base - 3}" width="3" height="5" fill="#6e7681"/>')
    art += tree(796, 192, 34) + tree(812, 192, 24) + tree(1110, 192, 40) + tree(1128, 192, 28)
    write("about.svg", svg(W, 214, body + art, "More about me"))


if __name__ == "__main__":
    header()
    section("title-connect.svg", "link", "Connect With Me")
    section("title-tech.svg", "laptop", "Tech Stack")
    section("title-stats.svg", "bars", "GitHub Stats")
    section("title-about.svg", "user", "More About Me")
    buttons()
    tech_stack()
    about()
