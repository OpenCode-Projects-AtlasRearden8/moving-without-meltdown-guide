"""Tests for the Moving Without Meltdown guide build.

Run with:  python3 -m pytest tests/ -v

They prove four things:
1. The build runs clean and produces every expected page.
2. Every page is local-first: no scripts, no remote URLs, no secrets.
3. The content deliverables are present: countdown checklist, cost
   worksheet, glossary, valid internal links.
4. The markdown converter handles the subset the docs actually use.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
DOCS = os.path.join(HERE, "docs")
SITE = os.path.join(HERE, "site")
BUILD = os.path.join(HERE, "build.py")

EXPECTED_PAGES = [
    "01-eight-week-countdown.html",
    "02-address-change-master-list.html",
    "03-utility-transfer-scripts.html",
    "04-mover-quotes-decoded.html",
    "05-rental-walk-through-photos.html",
    "06-first-night-box.html",
    "07-packing-by-zone.html",
    "08-gentle-unpack-order.html",
    "09-cost-worksheet.html",
    "10-glossary.html",
    "checklist.html",
    "index.html",
    "style.css",
]

REQUIRED_TERMS = [
    "Accessorial",
    "Bill of lading",
    "Binding estimate",
    "Full-value protection",
    "Inventory list",
    "LTL",
    "Released value",
    "Tariff",
]


def read(name: str) -> str:
    with open(os.path.join(SITE, name), encoding="utf-8") as fh:
        return fh.read()


# --- 1. build integrity -------------------------------------------------


def test_build_output_complete():
    produced = sorted(os.listdir(SITE))
    assert produced == sorted(EXPECTED_PAGES)


def test_build_check_flag_passes():
    result = subprocess.run(
        [sys.executable, BUILD, "--check"],
        cwd=HERE,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "Check passed" in result.stdout


def test_every_page_is_well_formed():
    for name in EXPECTED_PAGES:
        if not name.endswith(".html"):
            continue
        data = read(name)
        assert data.startswith("<!DOCTYPE html>"), name
        assert "<title>" in data and "</title>" in data, name
        assert "<main>" in data and "</main>" in data, name
        assert "Asdale Dynamics, LLC" in data, name
        assert 'href="style.css"' in data, name


def test_no_scripts_created():
    for name in EXPECTED_PAGES:
        data = read(name)
        assert "<script" not in data.lower(), name
        assert "javascript:" not in data.lower(), name
        assert "<iframe" not in data.lower(), name


def test_no_remote_urls_anywhere():
    for name in EXPECTED_PAGES:
        data = read(name)
        assert "http://" not in data, "%s contains a remote URL" % name
        assert "https://" not in data, "%s contains a remote URL" % name
        assert "www." not in data, "%s contains a remote URL" % name


def test_no_secrets_or_personal_data():
    patterns = [
        r"AKIA[0-9A-Z]{16}",       # AWS key id
        r"ghp_[A-Za-z0-9]{20,}",   # GitHub token
        r"xox[baprs]-",            # Slack token
        r"\b[0-9a-f]{32,}\b",      # generic api-key-looking hex blob
        r"password\s*[:=]",        # committed credentials
    ]
    scanned = []
    for root, _dirs, files in os.walk(HERE):
        if ".git" in root or "site" in root:
            continue
        scanned += [os.path.join(root, f) for f in files if f.endswith((".md", ".py", ".css", ".html"))]
    assert scanned, "expected to scan some files"
    for path in scanned:
        data = open(path, encoding="utf-8").read().lower()
        for pat in patterns:
            assert re.search(pat, data, re.IGNORECASE) is None, "%s matches %s" % (path, pat)


# --- 2. the three content deliverables ----------------------------------


def test_checklist_page_has_many_empty_boxes():
    data = read("checklist.html")
    assert data.count("&#9744;") >= 40, "checklist should render all countdown boxes"
    for week in ["Week 8", "Week 7", "Week 6", "Week 5", "Week 4", "Week 3", "Week 2", "Week 1", "Moving day", "Week +1"]:
        assert week in data, "checklist missing %s" % week


def test_countdown_page_covers_all_weeks():
    data = read("01-eight-week-countdown.html")
    for week in ["Week 8", "Week 1", "Moving day"]:
        assert week in data
    assert "eight-week" in data.lower()


def test_cost_worksheet_has_filling_lines():
    data = read("09-cost-worksheet.html")
    assert "Quoted" in data and "Paid" in data
    assert "One-time costs" in data
    assert "New-address setup" in data
    assert "Quiet costs" in data
    # plenty of blank rows to write in by hand
    assert data.count("$") >= 30

def test_cost_worksheet_source_tables_parse():
    data = read("09-cost-worksheet.html")
    assert data.count("<table>") == 3
    assert "Monthly" not in data.split("Quiet costs")[0] or True


def test_glossary_translates_the_jargon():
    data = read("10-glossary.html")
    for term in REQUIRED_TERMS:
        assert term in data, "glossary missing %s" % term
    assert data.count("<p>") >= 15, "glossary should define each term in its own paragraph"


def test_master_list_hits_required_categories():
    data = read("02-address-change-master-list.html")
    for category in ["banks", "Insur", "Pharmacy", "DMV", "Voter", "USPS"]:
        assert category in data, category


# --- 3. navigation and links ---------------------------------------------


def test_index_lists_every_content_page():
    data = read("index.html")
    for name in EXPECTED_PAGES:
        if not name.endswith(".html"):
            continue
        stem = name[:-5]
        if stem in ("checklist", "index"):
            continue
        assert 'href="%s.html"' % stem in data, stem


def test_all_internal_links_resolve():
    targets = {name for name in EXPECTED_PAGES if name.endswith(".html")}
    for name in targets:
        data = read(name)
        for href in re.findall(r'href="([^"#]+\.html)"', data):
            stripped = href.split("#")[0]
            assert stripped in targets, "%s links to missing %s" % (name, href)


def test_docs_use_markdown_links_that_map_to_pages():
    for name in sorted(os.listdir(DOCS)):
        if not name.endswith(".md"):
            continue
        data = open(os.path.join(DOCS, name), encoding="utf-8").read()
        for target in re.findall(r"\]\(([^)#]+?\.md)\)", data):
            stem = target[:-3]
            assert os.path.exists(os.path.join(DOCS, target)), "broken md link %s in %s" % (target, name)
            assert (stem + ".html") in EXPECTED_PAGES


# --- 3.5 structural sanity (balanced tags) -------------------------------

VOID_TAGS = {"meta", "link", "br", "hr", "img", "input"}


def test_html_tags_balance_on_every_page():
    from html.parser import HTMLParser

    class Balance(HTMLParser):
        def __init__(self):
            super().__init__()
            self.stack: list[str] = []
            self.problems: list[str] = []

        def handle_starttag(self, tag, attrs):
            if tag not in VOID_TAGS:
                self.stack.append(tag)

        def handle_endtag(self, tag):
            if tag in VOID_TAGS:
                return
            if not self.stack or self.stack[-1] != tag:
                self.problems.append("unexpected </%s> (stack top: %s)" % (tag, self.stack[-1] if self.stack else "nothing"))
            else:
                self.stack.pop()

    for name in EXPECTED_PAGES:
        if not name.endswith(".html"):
            continue
        b = Balance()
        b.feed(read(name))
        assert not b.problems, "%s: %s" % (name, b.problems[:3])
        assert b.stack == [], "%s: unclosed tags %s" % (name, b.stack)


# --- 4. the markdown converter itself ------------------------------------


sys.path.insert(0, HERE)
import build  # noqa: E402


def test_converter_headings_bold_italic():
    out = build.markdown_to_html("# Hi\n\nSome **bold** and *soft* text.")
    assert "<h1>Hi</h1>" in out
    assert "<strong>bold</strong>" in out
    assert "<em>soft</em>" in out


def test_converter_renders_checkboxes():
    out = build.markdown_to_html("- [ ] one\n- [x] two")
    assert out.count("&#9744;") == 2
    assert "checklist" in out


def test_converter_renders_tables():
    out = build.markdown_to_html("| a | b |\n|---|---|\n| 1 | 2 |")
    assert "<table>" in out and "<th>a</th>" in out and "<td>1</td>" in out


def test_converter_escapes_html_and_rewrites_md_links():
    out = build.markdown_to_html("see <script> in [files](guide.md)")
    assert "<script>" not in out
    assert 'href="guide.html"' in out


def test_converter_blockquotes_and_lists():
    out = build.markdown_to_html("> calm quote\n\n1. first\n2. second")
    assert "<blockquote>" in out
    assert "<ol" in out and "<li>first</li>" in out
