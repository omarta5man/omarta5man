"""Draw the terminal-green profile cards into assets/.

Run with GITHUB_TOKEN set (the Action passes its own token; locally:
`GITHUB_TOKEN=$(gh auth token) python scripts/build.py`). Only public repos
are read, so private project names never reach the profile.
"""

import datetime as dt
import json
import os
import urllib.request
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
LEVELS = ["#0f1a11", "#0e4429", "#006d32", "#26a641", "#3dff7a"]
LANG_SHADES = ["#3dff7a", "#26a641", "#ffb347", "#1b7f3f", "#9be9a8", "#2f4f38"]


def gql(query: str) -> dict:
    token = os.environ["GITHUB_TOKEN"]
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "profile-cards"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if "errors" in body:
        raise SystemExit(body["errors"])
    return body["data"]


def fetch() -> dict:
    return gql(
        """{ user(login: "%s") {
          repositories(ownerAffiliations: OWNER, privacy: PUBLIC, first: 100) {
            totalCount
            nodes { name description url stargazerCount forkCount isFork
              languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } } }
          }
          pullRequests(states: MERGED) { totalCount }
          contributionsCollection {
            totalCommitContributions totalPullRequestContributions totalIssueContributions
            contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
          }
        } }"""
        % LOGIN
    )["user"]


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


def stats(u):
    cc = u["contributionsCollection"]
    repos = [r for r in u["repositories"]["nodes"] if not r["isFork"]]
    stars = sum(r["stargazerCount"] for r in repos)
    skip = set(CONFIG.get("skip_languages", []))
    langs: dict[str, int] = {}
    for r in repos:
        for e in r["languages"]["edges"]:
            n = e["node"]["name"]
            if n not in skip:
                langs[n] = langs.get(n, 0) + e["size"]
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:5]
    other = total - sum(v for _, v in top)
    if other > 0:
        top.append(("Other", other))

    weeks = cc["contributionCalendar"]["weeks"][-53:]
    h = 400
    body = prompt(28, 62, f"gh stats --user {LOGIN} --year")
    tiles = [
        ("PUBLIC REPOS", len(repos)),
        ("COMMITS", cc["totalCommitContributions"]),
        ("PRS MERGED", u["pullRequests"]["totalCount"]),
        ("STARS", stars),
    ]
    for i, (k, v) in enumerate(tiles):
        x = 28 + i * 200
        body += t(x, 100, k, C["dim"], 11, 700, extra='letter-spacing="2"')
        body += f'<g filter="url(#glow)">{t(x, 140, v, C["green"], 36, 800)}</g>'
    # language bar
    x0, bw, y = 28, W - 56, 172
    x = x0
    for i, (n, v) in enumerate(top):
        w = bw * v / total
        body += f'<rect x="{x:.1f}" y="{y}" width="{max(w-2,1):.1f}" height="8" rx="2" fill="{LANG_SHADES[i % len(LANG_SHADES)]}"/>'
        x += w
    lx = x0
    for i, (n, v) in enumerate(top):
        label = f"{n} {100*v/total:.0f}%"
        body += f'<rect x="{lx}" y="{y+22}" width="9" height="9" rx="2" fill="{LANG_SHADES[i % len(LANG_SHADES)]}"/>'
        body += t(lx + 15, y + 31, label, C["text"], 12)
        lx += len(label) * 7.4 + 34
    # contribution grid
    gy = 236
    body += t(28, gy - 8, f"{cc['contributionCalendar']['totalContributions']} contributions in the last year", C["dim"], 12)
    cell, gap = 11, 3
    gx = 28 + (W - 56 - len(weeks) * (cell + gap)) / 2
    peak = max([d["contributionCount"] for w_ in weeks for d in w_["contributionDays"]] + [1])
    for wi, w_ in enumerate(weeks):
        for d in w_["contributionDays"]:
            dow = dt.date.fromisoformat(d["date"]).isoweekday() % 7
            n = d["contributionCount"]
            lvl = 0 if n == 0 else min(4, 1 + int(3 * n / peak))
            body += (f'<rect x="{gx + wi*(cell+gap):.1f}" y="{gy + dow*(cell+gap)}" width="{cell}" height="{cell}" rx="2" '
                     f'fill="{LEVELS[lvl]}"><title>{d["date"]}: {n}</title></rect>')
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    body += t(28, h - 22, f"# last sync {today}", C["dim"], 11)
    lg = W - 28 - 5 * 14 - 70
    body += t(lg - 8, h - 22, "less", C["dim"], 11, anchor="end")
    for i, col in enumerate(LEVELS):
        body += f'<rect x="{lg + i*14}" y="{h-32}" width="11" height="11" rx="2" fill="{col}"/>'
    body += t(lg + 5 * 14 + 4, h - 22, "more", C["dim"], 11)
    return frame(h, "~/activity — live", body)


def repo_card(r, fallback_desc):
    desc = (fallback_desc or r["description"] or "").strip()
    words, rows, cur = desc.split(), [], ""
    for wd in words:
        if len(cur) + len(wd) + 1 > 46:
            rows.append(cur)
            cur = wd
        else:
            cur = f"{cur} {wd}".strip()
    if cur:
        rows.append(cur)
    rows = rows[:3]
    edges = r["languages"]["edges"]
    lang = edges[0]["node"]["name"] if edges else "—"
    w, h = 412, 150
    body = t(22, 62, "~/", C["dim"], 15) + t(42, 62, r["name"][:38], C["green"], 15, 700)
    for i, row in enumerate(rows):
        body += t(22, 90 + i * 19, row, C["text"], 12.5)
    body += f'<circle cx="27" cy="{h-21}" r="5" fill="{C["amber"]}"/>' + t(38, h - 17, lang, C["text"], 12)
    body += t(w - 22, h - 17, f"★ {r['stargazerCount']}   ⑂ {r['forkCount']}", C["dim"], 12, anchor="end")
    return frame(h, "repo", body, w)


def footer():
    h = 64
    body = t(W / 2, 54, "[ process exited with code 0 ]  ·  thanks for visiting", C["dim"], 12, anchor="middle")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" font-family="{FONT}">
<line x1="28" y1="24" x2="{W-28}" y2="24" stroke="{C['line']}" stroke-dasharray="4 6"/>{body}</svg>
'''


def main():
    ASSETS.mkdir(exist_ok=True)
    u = fetch()
    out = {"hero.svg": hero(), "about.svg": about(), "stats.svg": stats(u), "footer.svg": footer()}
    by_name = {r["name"]: r for r in u["repositories"]["nodes"]}
    for name, fallback in CONFIG["featured"].items():
        if name in by_name:
            out[f"repo-{name}.svg"] = repo_card(by_name[name], fallback)
    for fn, svg in out.items():
        (ASSETS / fn).write_text(svg, encoding="utf-8")
    print("wrote", ", ".join(out))


if __name__ == "__main__":
    main()
