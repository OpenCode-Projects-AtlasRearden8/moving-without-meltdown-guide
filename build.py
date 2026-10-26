#!/usr/bin/env python3
"""Build script for the Moving Without Meltdown guide.

Converts docs/*.md into a local-first static HTML site in site/.
Standard library only: no installs, no network, no accounts.

Usage:
    python3 build.py            # build the site
    python3 build.py --quiet    # build with less output
    python3 build.py --check    # verify every expected page exists after build

Nothing in the output touches the internet: no external fonts, scripts,
or images are ever emitted.
"""

from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(HERE, "docs")
ASSETS_DIR = os.path.join(HERE, "assets")
OUT_DIR = os.path.join(HERE, "site")

SKIP_DOCS = {"00-start-here.md"}  # 00-start-here becomes the index page instead

CREDIT = "Asdale Dynamics, LLC"
TAGLINE = "A friend-paced guide to moving house without the meltdown."

NAV_EXTRA = [("checklist.html", "Printable checklist"), ("09-cost-worksheet.html", "Cost worksheet")]


# ---------------------------------------------------------------------------
# Tiny markdown -> HTML converter (stdlib only)
# Supports: headings, paragraphs, blockquotes, ul/ol with [ ] checkboxes,
# pipe tables, hr, bold/italic/inline code/links. Deliberately small.
# ---------------------------------------------------------------------------

_FENCE_RE = re.compile(r"^\s*```")


def _escape(text: str) -> str:
    return html.escape(text, quote=False).replace('"', "&quot;")


def _inline(text: str) -> str:
    text = _escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*\s][^*]*)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: '<a href="%s">%s</a>'
        % (m.group(2)[:-3] + ".html" if m.group(2).endswith(".md") else m.group(2), m.group(1)),
        text,
    )
    return text


def _is_table_row(line: str) -> bool:
    return line.lstrip().startswith("|") and line.rstrip().endswith("|")


def _split_row(line: str) -> list[str]:
    inner = line.strip().strip("|")
    return [c.strip() for c in inner.split("|")]


def markdown_to_html(md: str) -> str:
    """Convert the markdown subset used by docs/ into an HTML fragment."""
    md = md.replace("\r\n", "\n")
    lines = md.split("\n")
    out: list[str] = []
    i = 0
    para: list[str] = []

    def flush_para() -> None:
        if para:
            out.append("<p>%s</p>" % _inline(" ".join(para)))
            para.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            flush_para()
            i += 1
            continue

        if _FENCE_RE.match(line):
            flush_para()
            i += 1
            code: list[str] = []
            while i < len(lines) and not _FENCE_RE.match(lines[i]):
                code.append(lines[i])
                i += 1
            i += 1
            out.append("<pre><code>%s</code></pre>" % _escape("\n".join(code)))
            continue

        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            flush_para()
            level = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (level, _inline(m.group(2)), level))
            i += 1
            continue

        if stripped in ("---", "***", "___"):
            flush_para()
            out.append("<hr>")
            i += 1
            continue

        if stripped.startswith(">"):
            flush_para()
            quote: list[str] = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            while quote and not quote[-1].strip():
                quote.pop()
            while quote and not quote[0].strip():
                quote.pop(0)
            out.append("<blockquote>%s</blockquote>" % markdown_to_html("\n".join(quote)))
            continue

        if _is_table_row(stripped) and i + 1 < len(lines) and re.match(r"^\s*\|[\s:\-|]+\|\s*$", lines[i + 1]):
            flush_para()
            header = _split_row(stripped)
            i += 2
            rows: list[list[str]] = []
            while i < len(lines) and _is_table_row(lines[i].strip()):
                rows.append(_split_row(lines[i].strip()))
                i += 1
            cells = "".join("<th>%s</th>" % _inline(c) for c in header)
            out.append("<table><thead><tr>%s</tr></thead>" % cells)
            body_cells = "".join(
                "<tr>%s</tr>" % "".join("<td>%s</td>" % _inline(c) for c in row) for row in rows
            )
            out.append("<tbody>%s</tbody></table>" % body_cells)
            continue

        m = re.match(r"^[-*]\s+\[([ xX])\]\s+(.*)$", stripped)
        if m:
            flush_para()
            items: list[tuple[bool, str]] = [(m.group(1).lower() == "x", m.group(2))]
            i += 1
            while i < len(lines):
                m2 = re.match(r"^\s*[-*]\s+\[([ xX])\]\s+(.*)$", lines[i])
                if not m2:
                    break
                items.append((m2.group(1).lower() == "x", m2.group(2)))
                i += 1
            cells = "".join(
                '<li class="check"><span class="box">&#9744;</span> %s</li>' % _inline(text)
                for _, text in items
            )
            out.append('<ul class="checklist">%s</ul>' % cells)
            continue

        m = re.match(r"^[-*]\s+(.*)$", stripped)
        if m:
            flush_para()
            items = [m.group(1)]
            i += 1
            while i < len(lines) and re.match(r"^\s*[-*]\s+\S", lines[i]):
                items.append(re.match(r"^\s*[-*]\s+(.*)$", lines[i]).group(1))
                i += 1
            out.append("<ul>%s</ul>" % "".join("<li>%s</li>" % _inline(t) for t in items))
            continue

        m = re.match(r"^(\d+)[.)]\s+(.*)$", stripped)
        if m:
            flush_para()
            items = [m.group(2)]
            num = m.group(1)
            i += 1
            while i < len(lines) and re.match(r"^\s*\d+[.)]\s+\S", lines[i]):
                items.append(re.match(r"^\s*\d+[.)]\s+(.*)$", lines[i]).group(1))
                i += 1
            out.append(
                '<ol start="%s">%s</ol>' % (num, "".join("<li>%s</li>" % _inline(t) for t in items))
            )
            continue

        para.append(stripped)
        i += 1

    flush_para()
    return "\n".join(out)


def first_heading(md: str) -> str:
    for line in md.split("\n"):
        m = re.match(r"^#\s+(.+)$", line.strip())
        if m:
            return m.group(1).strip()
    return "Untitled"


# ---------------------------------------------------------------------------
# Page assembly
# ---------------------------------------------------------------------------


def page_shell(title: str, body: str, active: str = "") -> str:
    nav_links = ['<a href="index.html">Home</a>']
    for href, label in NAV_EXTRA:
        cls = ' class="active"' if href == active else ""
        nav_links.append('<a href="%s"%s>%s</a>' % (href, cls, label))
    nav = "\n".join(nav_links)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_escape(title)} — Moving Without Meltdown</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<header class="masthead">
  <p class="kicker">{_escape(TAGLINE)}</p>
  <nav>{nav}</nav>
</header>
<main>
{body}
</main>
<footer>
  <p>Moving Without Meltdown &middot; built locally, never online &middot; {CREDIT}</p>
</footer>
</body>
</html>
"""


def build_checklist_page(countdown_md: str) -> str:
    """Derive a one-page printable checklist from the countdown markdown."""
    parts: list[str] = ['<h1>The whole countdown, one page</h1>']
    parts.append(
        "<p>Print this, stick it on the fridge, and let each week tell you "
        "exactly what to do. Details live on the linked pages in the site.</p>"
    )
    lines = countdown_md.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^(#{1,3})\s+(.*)$", line.strip())
        if m:
            level = min(len(m.group(1)) + 1, 4)
            parts.append("<h%d>%s</h%d>" % (level, _inline(m.group(2)), level))
            i += 1
            continue
        m = re.match(r"^\s*[-*]\s+\[([ xX])\]\s+(.*)$", line)
        if m:
            items: list[str] = [m.group(2)]
            i += 1
            while i < len(lines) and re.match(r"^\s*[-*]\s+\[[ xX]\]\s+\S", lines[i]):
                items.append(re.match(r"^\s*[-*]\s+\[[ xX]\]\s+(.*)$", lines[i]).group(1))
                i += 1
            cells = "".join(
                '<li class="check"><span class="box">&#9744;</span> %s</li>' % _inline(t)
                for t in items
            )
            parts.append('<ul class="checklist">%s</ul>' % cells)
            continue
        i += 1
    parts.append(
        '<hr><p class="finePrint">Calmdown tip: if a week gets away from you, '
        "roll the unfinished boxes into the next week instead of starting over. "
        "The schedule serves you; you do not serve the schedule.</p>"
    )
    return "\n".join(parts)


def write_page(name: str, title: str, body: str) -> None:
    path = os.path.join(OUT_DIR, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(page_shell(title, body, active=name))
    return None


def build(quiet: bool = False) -> list[str]:
    os.makedirs(OUT_DIR, exist_ok=True)

    docs = sorted(f for f in os.listdir(DOCS_DIR) if f.endswith(".md"))
    if not docs:
        raise SystemExit("No markdown docs found in docs/ - nothing to build.")

    rendered: dict[str, str] = {}

    for name in docs:
        with open(os.path.join(DOCS_DIR, name), encoding="utf-8") as fh:
            md = fh.read()
        stem = name[:-3]
        rendered[stem] = md

    pages: list[str] = []

    # Index page: hand-built, calm, with room to breathe.
    toc_rows = []
    for stem, md in rendered.items():
        if stem == "00-start-here":
            continue
        toc_rows.append(
            '<li><a href="%s.html">%s</a></li>' % (stem, _escape(first_heading(md)))
        )
    intro_body = markdown_to_html(rendered["00-start-here"])
    index_html = intro_body + (
        "\n<section class='card toc'>\n<h2>Every page, one tap away</h2>\n"
        "<ul class='tocList'>\n%s\n</ul>\n</section>\n" % "\n".join(toc_rows)
    )
    write_page("index.html", "Start here", index_html)
    pages.append("index.html")

    # Regular doc pages.
    for stem, md in rendered.items():
        if stem == "00-start-here":
            continue
        body = markdown_to_html(md)
        write_page("%s.html" % stem, first_heading(md), body)
        pages.append("%s.html" % stem)

    # Derived printable checklist from the countdown doc.
    if "01-eight-week-countdown" in rendered:
        body = build_checklist_page(rendered["01-eight-week-countdown"])
        write_page("checklist.html", "Printable checklist", body)
        pages.append("checklist.html")

    # Stylesheet.
    shutil.copyfile(os.path.join(ASSETS_DIR, "style.css"), os.path.join(OUT_DIR, "style.css"))

    if not quiet:
        print("Built %d pages + stylesheet into site/" % len(pages))
    return pages


def check(pages: list[str] | None = None) -> int:
    """Sanity check that every expected page exists and is plausible HTML."""
    if pages is None:
        pages = sorted(
            f for f in os.listdir(OUT_DIR) if f.endswith(".html") or f.endswith(".css")
        )
    problems = []
    for name in pages:
        path = os.path.join(OUT_DIR, name)
        if not os.path.exists(path):
            problems.append("missing: %s" % name)
            continue
        data = open(path, encoding="utf-8").read()
        if name.endswith(".html"):
            if not data.startswith("<!DOCTYPE html>"):
                problems.append("%s: missing DOCTYPE" % name)
            if "<title>" not in data:
                problems.append("%s: missing title" % name)
            if "http://" in data or "https://" in data:
                problems.append("%s: contains a remote URL" % name)
    if problems:
        for p in problems:
            print("CHECK FAIL: %s" % p, file=sys.stderr)
        return 1
    if not getattr(check, "_quiet", False):
        print("Check passed: %d files, all local, all titled." % len(pages))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Moving Without Meltdown site.")
    parser.add_argument("--quiet", action="store_true", help="less output")
    parser.add_argument("--check", action="store_true", help="verify pages after building")
    args = parser.parse_args()
    pages = build(quiet=args.quiet)
    if args.check:
        check._quiet = args.quiet
        sys.exit(check(pages))
    return 0


if __name__ == "__main__":
    sys.exit(main())
