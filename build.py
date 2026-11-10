#!/usr/bin/env python3
"""Build a self-contained HTML graph of Claude Code memories.

Reads <config>/projects/*/memory/*.md (config = $CLAUDE_CONFIG_DIR or ~/.claude),
groups memory dirs into workspaces, resolves [[links]] between memories, and writes
one HTML file with no external dependencies.
"""
import argparse, datetime, json, os, pathlib, re

HERE = pathlib.Path(__file__).resolve().parent
# Folders people keep repos in; stripped so "~/Projects/acme-api" groups as "acme".
CONTAINERS = {"projects", "developer", "dev", "code", "src", "repos", "git", "github",
              "workspace", "workspaces", "work", "documents", "sites"}


def encode(path):
    """Claude Code names a project dir after its cwd with every non-alphanumeric char as '-'."""
    return re.sub(r"[^A-Za-z0-9]", "-", str(path))


def project_label(dirname, home_enc):
    """'-Users-ana-Projects-acme-api' -> 'acme-api'; the home dir itself -> 'home'."""
    if dirname == home_enc:
        return "home"
    label = dirname[len(home_enc) + 1:] if dirname.startswith(home_enc + "-") else dirname.lstrip("-")
    head, _, rest = label.partition("-")
    if head.lower() in CONTAINERS and rest:
        label = rest
    return label or "home"


def workspaces(labels):
    """Group labels under the shortest other label that prefixes them on a '-' boundary.

    ['acme', 'acme-api', 'acme-web', 'blog'] -> acme: acme, acme-api, acme-web; blog: blog.
    Dashes in folder names are ambiguous, so this only groups when the parent dir exists too.
    """
    out = {}
    for l in labels:
        parents = [p for p in labels if p != l and l.startswith(p + "-")]
        out[l] = min(parents, key=len) if parents else l
    return out


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    fm = {}
    for line in m.group(1).splitlines():
        mm = re.match(r"^\s*([A-Za-z_]+):\s*(.*)$", line)  # also catches keys nested under metadata:
        if mm and mm.group(2).strip():
            fm.setdefault(mm.group(1), mm.group(2).strip().strip('"\''))
    return fm, m.group(2)


def read_toml_colors(path):
    """Tiny TOML reader for flat color files: returns {"section.key" or "key": "#hex"}.
    shortcut: handles `key = "value"` lines and [section] headers only; enough for theme files."""
    out, section = {}, ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.split("#", 1)[0] if not re.search(r'=\s*["\']#', line) else line
        line = line.strip()
        m = re.match(r"^\[([^\]]+)\]$", line)
        if m:
            section = m.group(1).strip()
            continue
        m = re.match(r'^([\w.-]+)\s*=\s*["\'](#?[0-9A-Za-z_ .-]+)["\']', line)
        if m:
            out[(section + "." if section else "") + m.group(1)] = m.group(2)
    return out


def _hex(c):
    c = (c or "").strip().lstrip("#").replace("0x", "")
    return "#" + c[:6] if re.fullmatch(r"[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?", c) else None


def _hue(hexc):
    r, g, b = (int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5))
    mx, mn = max(r, g, b), min(r, g, b)
    if mx == mn:
        return 0
    d = mx - mn
    h = (g - b) / d % 6 if mx == r else (b - r) / d + 2 if mx == g else (r - g) / d + 4
    return round(h * 60) % 360


def _rgba(hexc, a):
    return "rgba(%d,%d,%d,%s)" % (int(hexc[1:3], 16), int(hexc[3:5], 16), int(hexc[5:7], 16), a)


def omarchy_theme(home):
    """Read the active Omarchy theme (if any) and map it onto the page's theme tokens."""
    for d in (home / ".local/state/omarchy/current/theme", home / ".config/omarchy/current/theme"):
        if not d.exists():
            continue
        c = {}
        if (d / "colors.toml").exists():
            c = {k: _hex(v) for k, v in read_toml_colors(d / "colors.toml").items()}
        elif (d / "alacritty.toml").exists():  # older themes: derive from the terminal palette
            a = {k: _hex(v) for k, v in read_toml_colors(d / "alacritty.toml").items()}
            c = {"background": a.get("colors.primary.background"), "foreground": a.get("colors.primary.foreground"),
                 "muted": a.get("colors.bright.black"), "accent": a.get("colors.normal.blue"),
                 **{n: a.get("colors.normal." + n) for n in ("red", "green", "yellow", "blue", "magenta", "cyan")}}
        bg, fg = c.get("background") or c.get("bg"), c.get("foreground") or c.get("fg")
        if not (bg and fg):
            continue
        hues = [_hue(c[n]) for n in ("blue", "green", "magenta", "yellow", "cyan", "red") if c.get(n)]
        light = sum(int(bg[i:i + 2], 16) for i in (1, 3, 5)) > 384
        accent = c.get("accent") or c.get("blue") or fg
        surface = c.get("lighter_background") or bg
        font = None
        alac = home / ".config/alacritty/alacritty.toml"
        if alac.exists():
            font = read_toml_colors(alac).get("font.normal.family")
        name_file = d.parent / "theme.name"  # Omarchy stages a copy, so the dir name isn't the theme name
        name = (name_file.read_text(encoding="utf-8").strip() if name_file.exists()
                else d.resolve().name if d.resolve().name != "theme" else "current")
        tokens = {
            "--bg": bg, "--surface": surface, "--ink": fg,
            "--muted": c.get("muted") or c.get("dark_foreground") or _rgba(fg, .6),
            "--line": c.get("lighter_background") or _rgba(fg, .15),
            "--edge": _rgba(fg, .13), "--edge-hi": accent, "--hub": c.get("bright_foreground") or fg,
            "--focus": accent, "--sat": "62", "--lum": "44" if light else "62", "--region": ".06",
            "--glow": "0", "--grid": "transparent", "--hues": ",".join(map(str, hues)),
            "--card-bg": _rgba(surface, .88), "--card-border": "1px solid " + _rgba(fg, .14),
            "--card-blur": "blur(10px)", "--card-shadow": "0 10px 30px " + _rgba("#000000", .35 if not light else .12),
            "--radius": "10px", "--field": c.get("darker_background") or c.get("dark_background") or bg,
        }
        if font:
            tokens["--font"] = '"%s",ui-monospace,Menlo,monospace' % font.replace('"', "")
        return {"name": name, "tokens": tokens,
                "preview": {"bg": bg, "dots": [c.get(n) or accent for n in ("blue", "magenta", "green")]}}
    return None


# Brand fonts for the Claude theme (SIL OFL, see fonts/OFL-*.txt), embedded so the page stays offline.
FONTS = [("Poppins-400.woff2", "Poppins", "400", "normal"), ("Poppins-600.woff2", "Poppins", "600", "normal"),
         ("Poppins-600-Italic.woff2", "Poppins", "600", "italic"),
         ("Lora-wght.woff2", "Lora", "400 700", "normal"), ("Lora-Italic-wght.woff2", "Lora", "400 700", "italic")]


def font_css(font_dir=HERE / "fonts"):
    """@font-face rules with base64 woff2 data; missing files are skipped (page falls back to system fonts)."""
    import base64
    out = []
    for name, family, weight, style in FONTS:
        f = font_dir / name
        if f.exists():
            data = base64.b64encode(f.read_bytes()).decode("ascii")
            out.append(f"@font-face{{font-family:'{family}';font-style:{style};font-weight:{weight};"
                       f"font-display:swap;src:url(data:font/woff2;base64,{data}) format('woff2')}}")
    return "\n".join(out)


def build(root, home, bodies=True):
    home_enc = encode(home)
    raw = []
    for d in sorted(os.listdir(root)):
        mdir = root / d / "memory"
        # skip temp/scratch session dirs
        if not mdir.is_dir() or d.startswith(("-private-", "-tmp-", "-var-folders-")) or "-AppData-Local-Temp-" in d:
            continue
        files = [f for f in sorted(mdir.glob("*.md")) if f.name != "MEMORY.md"]
        if files:
            raw.append((project_label(d, home_enc), files))

    ws = workspaces([p for p, _ in raw])
    nodes, by_name, by_stem = [], {}, {}
    for proj, files in raw:
        for f in files:
            text = f.read_text(encoding="utf-8", errors="replace")  # explicit: Windows defaults to cp1252
            fm, body = frontmatter(text)
            n = {"id": f"{proj}/{f.stem}", "project": proj, "workspace": ws[proj],
                 "file": str(f).replace(str(home), "~", 1),
                 "name": fm.get("name", f.stem), "desc": fm.get("description", ""),
                 "type": fm.get("type", "unknown"),
                 "date": datetime.date.fromtimestamp(f.stat().st_mtime).isoformat(),
                 "size": len(text), "links": re.findall(r"\[\[([^\]|#]+)", body)}
            if bodies:
                n["body"] = body.strip()[:20000]  # cap: one runaway file shouldn't bloat the page
            nodes.append(n)
            by_name.setdefault(n["name"].lower(), []).append(n)
            by_stem.setdefault(f.stem.lower(), []).append(n)

    def resolve(target, src):
        t = target.strip().lower()
        cands = by_name.get(t, []) + by_stem.get(t, []) + by_stem.get(t.replace("-", "_"), [])
        same = [c for c in cands if c["project"] == src["project"]]
        return (same or cands or [None])[0]

    edges, dangling = [], 0
    for n in nodes:
        for l in n.pop("links"):
            t = resolve(l, n)
            if t is None:
                dangling += 1
            elif t["id"] != n["id"]:
                edges.append({"s": n["id"], "t": t["id"]})

    ids = {n["id"] for n in nodes}
    assert len(ids) == len(nodes), "duplicate node ids"
    assert all(e["s"] in ids and e["t"] in ids for e in edges), "edge to unknown node"
    return {"nodes": nodes, "edges": edges, "dangling": dangling,
            "built": datetime.date.today().isoformat(), "omarchy": omarchy_theme(home)}


def write_sidecar(out, theme):
    """Write <graph>.theme.js beside the graph. The open page re-reads it every couple of seconds, so a
    theme-set hook that rewrites it (--theme-only) re-themes the page live, without a rebuild or reload."""
    side = out.with_name(out.stem + ".theme.js")
    theme = {k: v for k, v in theme.items() if k != "sidecar"}
    tmp = side.with_name(side.name + ".tmp")
    tmp.write_text("window.__cmgOmarchy&&window.__cmgOmarchy(%s);\n" % json.dumps(theme), encoding="utf-8")
    os.replace(tmp, side)  # atomic, so the page never reads a half-written file
    return side


def main():
    config = pathlib.Path(os.environ.get("CLAUDE_CONFIG_DIR", pathlib.Path.home() / ".claude"))
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("out", nargs="?", default="memory-graph.html", help="output HTML path")
    ap.add_argument("--root", default=str(config / "projects"), help="Claude projects dir")
    ap.add_argument("--home", default=str(pathlib.Path.home()), help="home dir used to shorten labels")
    ap.add_argument("--no-bodies", action="store_true",
                    help="leave out memory text (names and descriptions only), e.g. for a graph you'll share")
    ap.add_argument("--theme-only", action="store_true",
                    help="only rewrite the Omarchy theme sidecar next to an existing graph (for a theme-set hook)")
    a = ap.parse_args()

    if a.theme_only:
        out = pathlib.Path(a.out).expanduser()
        theme = omarchy_theme(pathlib.Path(a.home).expanduser())
        if theme and out.exists():
            print(f"Omarchy theme '{theme['name']}' -> {write_sidecar(out, theme)}")
        return

    data = build(pathlib.Path(a.root).expanduser(), pathlib.Path(a.home).expanduser(), bodies=not a.no_bodies)
    out = pathlib.Path(a.out).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    # '</' would end the inline <script> early if a description contained '</script>'
    if data["omarchy"]:
        data["omarchy"]["sidecar"] = write_sidecar(out, data["omarchy"]).name
    payload = json.dumps(data).replace("</", "<\\/")
    template = (HERE / "template.html").read_text(encoding="utf-8")
    page = template.replace("/*__FONTS__*/", font_css()).replace("/*__DATA__*/null", payload)
    out.write_text(page, encoding="utf-8")
    print(f"{len(data['nodes'])} memories, {len(data['edges'])} links, {data['dangling']} dangling, "
          f"{len({n['project'] for n in data['nodes']})} projects, "
          f"{len({n['workspace'] for n in data['nodes']})} workspaces"
          + (f", Omarchy theme '{data['omarchy']['name']}'" if data["omarchy"] else "") + f" -> {out}")


if __name__ == "__main__":
    main()
