# claude-memory-graph

A [Claude Code](https://claude.com/claude-code) skill that turns your memories into an interactive graph. Every memory in `~/.claude/projects/*/memory/` becomes a node. Nodes cluster by project, projects group into workspaces, and `[[links]]` between memories become edges.

The output is one self-contained HTML file. It needs no server, makes no network calls and has no dependencies, so you can open it from anywhere.

**[✧ Try the live demo](https://jubs.studio/claude-memory-graph/)**, built from a fictional memory set, so no install is needed.

![Cycling through the Paper, Ink, Blueprint, Claude, Cursor and Cyber themes on a demo memory set, then searching and opening a memory](docs/demo.gif)

![claude-memory-graph in the Ink theme: workspaces as regions, a memory opened in the side reader](docs/screenshot.png)

## Why

I asked Claude to remove one stale memory, and it quietly updated several others along the way. That's when it clicked: Claude's memory isn't a list, it's a graph, and I had no way to see it. This is the view I wanted: every memory, how the memories link, and what a change might ripple into.

## Install

```bash
git clone https://github.com/jubscodes/claude-memory-graph ~/.claude/skills/claude-memory-graph
```

Then ask Claude: *"show me my memory graph"*.

## Run it directly

```bash
python3 ~/.claude/skills/claude-memory-graph/build.py ~/claude-memory-graph.html
```

| Option | Default |
|---|---|
| `out` (positional) | `memory-graph.html` |
| `--root` | `$CLAUDE_CONFIG_DIR/projects`, else `~/.claude/projects` |
| `--home` | your home dir (used to shorten project labels) |
| `--no-bodies` | off: memory text is included. Turn it on to keep only names and descriptions, e.g. for a graph you'll share |

Requires Python 3.8+, standard library only. Tested on macOS and Linux (Omarchy). It should also run on Windows; reports are welcome. On Windows, use `python` or `py` instead of `python3`, with the path `%USERPROFILE%\.claude\skills\claude-memory-graph\build.py`.

## What you see

- **Workspaces** are dashed regions. `~/Projects/acme`, `~/Projects/acme-api` and `~/Projects/acme-web` all group under `acme`.
- **Projects** are dark hubs, with their memories orbiting them.
- **Shape** shows the memory type: ● project, ◆ feedback, ■ reference, ▲ user.
- **Size** grows with the number of links.
- **Search** opens a side list of matching memories, grouped by workspace. Click a result to jump to it.
- **Reader:** click a memory to read its full text, lightly formatted. `[[links]]` inside it jump to the linked memory.
- **Themes:** Auto, Paper, Ink, Blueprint, Neon, Print, Claude, Cursor, Skeuo (linen, stitches & gloss) and Cyber (a green-phosphor terminal), chosen from the theme menu. Claude and Cursor are palettes inspired by those apps, not official themes.
- **Legend:** click a workspace, project or type to focus it, and click it again to show everything. ⇧-click adds or removes items, hovering previews them on the graph, and "Show all" resets the filters.

## Themes

| | |
|---|---|
| ![Cyber: green-phosphor terminal](docs/themes/cyber.png) **Cyber** | ![Claude: warm clay and ivory](docs/themes/claude.png) **Claude** |
| ![Blueprint: drafting-table blue](docs/themes/blueprint.png) **Blueprint** | ![Cursor: editor dark](docs/themes/cursor.png) **Cursor** |
| ![Paper: warm light](docs/themes/paper.png) **Paper** | ![The memory reader in Cyber, with links in both directions](docs/themes/reader.png) **Reader** |

Screenshots use the fictional demo set: a developer who names every project after a show.

**On [Omarchy](https://omarchy.org)?** The builder reads your active Omarchy theme (`colors.toml`, or `alacritty.toml` on older themes) and adds a matching **Omarchy** theme, which the page uses by default. To have an open graph follow theme switches live, install the bundled hook once: `omarchy hook install theme-set ~/.claude/skills/claude-memory-graph/hooks/omarchy-theme-set`. Without it, rebuild the graph after switching themes.

## Privacy

The HTML embeds each memory's name, description and full text (use `--no-bodies` to leave the text out). Treat it like the memories themselves. Check what's in it before you share it, and don't commit generated graphs. The `.gitignore` here excludes them.

## Development

```bash
python3 -I test_build.py
```

For screenshots and demos without your own memories, generate a fictional memory set and build from it:

```bash
python3 demo/make_demo.py
python3 build.py --root demo/projects --home /Users/ana demo/index.html
```

`build.py` parses memories and writes the data into `template.html`. The template holds the canvas renderer and force layout in plain JavaScript.

## Author

Made by Julia Hoffmann Buratto ✧ priestess of the harness fortress ✧

- GitHub: [@jubscodes](https://github.com/jubscodes)
- X: [@hoffz_eth](https://x.com/hoffz_eth)

If the graph showed you something about your memories, ⭐ [star the repo](https://github.com/jubscodes/claude-memory-graph). It helps other Claude Code users find it.

## License

MIT. The Claude theme embeds Poppins and Lora (SIL Open Font License 1.1); their licenses are in `fonts/`. The Claude and Cursor themes are palettes inspired by those apps, not official themes.
