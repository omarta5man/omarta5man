"""Draw the terminal-green profile cards into assets/.

Run: `python scripts/build.py`. The text comes from profile.json.
"""

import json
from pathlib import Path
from xml.sax.saxutils import escape

LOGIN = "omarta5man"
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
CONFIG = json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))

W = 840
FONT = "'JetBrains Mono','Fira Code','Cascadia Code',Consolas,'Courier New',ui-monospace,monospace"
C = {
    "bg": "#070b07",
    "panel": "#0b120b",
    "line": "#1c3a22",
    "green": "#3dff7a",
    "mid": "#22b455",
    "dim": "#5f8f6a",
    "text": "#c6f5d2",
    "amber": "#ffb347",
    "red": "#ff5f56",
    "yellow": "#ffbd2e",
    "lime": "#27c93f",
}


# ---------- drawing helpers ----------

def t(x, y, s, fill=None, size=14, weight=400, anchor="start", extra=""):
    fill = fill or C["text"]
    return (f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" font-weight="{weight}" '
            f'text-anchor="{anchor}" {extra}>{escape(str(s))}</text>')


def frame(h, title, body, width=W):
    """A terminal window: title bar with traffic lights, scanlines, glow."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{h}" viewBox="0 0 {width} {h}" font-family="{FONT}">
<defs>
  <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#3dff7a" opacity="0.035"/></pattern>
  <filter id="glow" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <linearGradient id="vig" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3dff7a" stop-opacity="0.05"/><stop offset="1" stop-color="#3dff7a" stop-opacity="0"/></linearGradient>
</defs>
<rect x="0.5" y="0.5" width="{width-1}" height="{h-1}" rx="10" fill="{C['bg']}" stroke="{C['line']}"/>
<rect x="1" y="1" width="{width-2}" height="30" rx="10" fill="{C['panel']}"/>
<rect x="1" y="20" width="{width-2}" height="11" fill="{C['panel']}"/>
<line x1="1" y1="31" x2="{width-1}" y2="31" stroke="{C['line']}"/>
<circle cx="20" cy="16" r="5.5" fill="{C['red']}"/><circle cx="38" cy="16" r="5.5" fill="{C['yellow']}"/><circle cx="56" cy="16" r="5.5" fill="{C['lime']}"/>
{t(width/2, 20.5, title, C['dim'], 12, anchor="middle")}
<rect x="1" y="32" width="{width-2}" height="{h-33}" rx="9" fill="url(#vig)"/>
{body}
<rect x="1" y="32" width="{width-2}" height="{h-33}" rx="9" fill="url(#scan)" pointer-events="none"/>
</svg>
'''


def prompt(x, y, cmd, size=14):
    """One <text> with tspans, so spacing holds whatever monospace font loads."""
    return (f'<text x="{x}" y="{y}" font-size="{size}" xml:space="preserve">'
            f'<tspan fill="{C["green"]}" font-weight="700">{LOGIN}@birzeit</tspan>'
            f'<tspan fill="{C["text"]}">:</tspan><tspan fill="{C["amber"]}" font-weight="700">~</tspan>'
            f'<tspan fill="{C["text"]}">$ {escape(cmd)}</tspan></text>')


def prompt_end(x, size=14, cmd=""):
    return x + (len(LOGIN) + 13 + len(cmd)) * size * 0.6


_clip_id = [0]


def typed(x, y, s, start, dur, fill, size, weight=400, glow=False):
    """Text that types itself out through a clip whose width steps open.
    The clip's own width is the full text, so without SMIL the text just shows."""
    _clip_id[0] += 1
    cid = f"type{_clip_id[0]}"
    cw = size * 0.62
    full = len(s) * cw + 2000
    n = len(s)
    total = start + dur
    kt = [0.0] + [(start + dur * i / n) / total for i in range(n + 1)]
    ws = [0.0] + [i * cw for i in range(n + 1)]
    ws[-1] = full
    g = ' filter="url(#glow)"' if glow else ""
    return (f'<clipPath id="{cid}"><rect x="{x - 4}" y="{y - size - 4}" width="{full}" height="{size * 2}">'
            f'<animate attributeName="width" begin="0s" dur="{total}s" fill="freeze" calcMode="discrete" '
            f'keyTimes="{";".join(f"{k:.4f}" for k in kt)}" values="{";".join(f"{v:.1f}" for v in ws)}"/></rect></clipPath>'
            f'<g clip-path="url(#{cid})"{g}>{t(x, y, s, fill, size, weight)}</g>')


def cursor(x, y, size, begin=0):
    return (f'<rect x="{x}" y="{y - size + 2}" width="{size*0.6:.1f}" height="{size + 2}" fill="{C["green"]}" opacity="0">'
            f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.01;0.5;0.51" dur="1s" begin="{begin}s" repeatCount="indefinite"/></rect>')


# ---------- cards ----------

def hero():
    name = CONFIG["name"]
    body = prompt(28, 66, "whoami")
    body += typed(28, 128, name, 0.4, 0.9, C["green"], 46, 800, glow=True)
    body += f'<line x1="28" y1="146" x2="{28 + len(name)*46*0.62:.0f}" y2="146" stroke="{C["mid"]}" stroke-width="2" stroke-dasharray="6 4"/>'
    body += typed(28, 180, CONFIG["tagline"], 1.5, 1.6, C["amber"], 15)
    body += typed(28, 208, CONFIG["subline"], 3.2, 1.4, C["dim"], 13)
    body += prompt(28, 252, "")
    body += cursor(prompt_end(28), 252, 14, 4.6)
    # right-side ascii chip
    chip = [
        "   ┌─┴─┴─┴─┴─┐   ",
        " ──┤  ESP32  ├── ",
        " ──┤  ░░░░░  ├── ",
        " ──┤  S3 ◉   ├── ",
        "   └─┬─┬─┬─┬─┘   ",
    ]
    for i, row in enumerate(chip):
        body += t(W - 34, 92 + i * 22, row, C["mid"], 15, 400, "end", 'opacity="0.85" xml:space="preserve"')
    return frame(282, f"{LOGIN} — bash — 80×24", body)


def about():
    lines = CONFIG["about"]
    h = 70 + len(lines) * 24 + 58
    body = prompt(28, 62, "cat about.txt")
    for i, ln in enumerate(lines):
        y = 96 + i * 24
        body += t(28, y, "▸", C["amber"], 14) + t(48, y, ln, C["text"], 14)
    body += prompt(28, h - 22, "")
    body += cursor(prompt_end(28), h - 22, 14)
    return frame(h, "~/about.txt", body)


def footer():
    h = 64
    body = t(W / 2, 54, "[ process exited with code 0 ]  ·  thanks for visiting", C["dim"], 12, anchor="middle")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" font-family="{FONT}">
<line x1="28" y1="24" x2="{W-28}" y2="24" stroke="{C['line']}" stroke-dasharray="4 6"/>{body}</svg>
'''


def main():
    ASSETS.mkdir(exist_ok=True)
    out = {"hero.svg": hero(), "about.svg": about(), "footer.svg": footer()}
    for fn, svg in out.items():
        (ASSETS / fn).write_text(svg, encoding="utf-8")
    print("wrote", ", ".join(out))


if __name__ == "__main__":
    main()
