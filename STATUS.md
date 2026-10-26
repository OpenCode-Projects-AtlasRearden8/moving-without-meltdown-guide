# STATUS.md

Project: **Moving Without Meltdown Guide** — a friend-paced moving manual,
in markdown docs, with a tested local-first static HTML site.
Status: **complete, verified 2026-10-26.**

## What was built

- **`docs/`** — the manual's 11 markdown pages:
  1. `00-start-here.md` — how the manual works, the three rules
  2. `01-eight-week-countdown.md` — weeks 8 through 1 plus moving day
  3. `02-address-change-master-list.md` — banks, DMV, insurers, pharmacy, voters, USPS, and the two-minute version
  4. `03-utility-transfer-scripts.md` — word-for-word phone scripts (electric/gas, water, internet, trash) + meter photos + overlap trick
  5. `04-mover-quotes-decoded.md` — weight vs. hours pricing, what to compare, red flags, tipping norms
  6. `05-rental-walk-through-photos.md` — move-in/out photo sets and the deposit logic
  7. `06-first-night-box.md` — the box that rides with you, not the truck
  8. `07-packing-by-zone.md` — zone order table, labeling system, "do not pack" shelf
  9. `08-gentle-unpack-order.md` — one-zone-per-evening rhythm for a working week
  10. `09-cost-worksheet.md` — Quoted/Paid worksheet covering one-time, setup, and quiet costs
  11. `10-glossary.md` — 19 moving-industry terms translated (LTL, tariff, bill of lading, SIT, accessorials…)
- **`build.py`** — pure-stdlib static site generator (no installs, no network):
  converts every doc to HTML, generates `index.html` with a full table of
  contents, derives a one-page printable countdown `checklist.html`, copies
  the stylesheet, and links `.md` targets to `.html` pages automatically.
  Flags: `--quiet`, `--check`.
- **`assets/style.css`** — one calm stylesheet (serif body, checkbox lists,
  print rules; no web fonts, no scripts, no remote anything).
- **`site/`** — the built output (12 pages + stylesheet; gitignored, rebuild in 1 second).
- **`GUIDE.md`** — five-minute friendly tour for first-time readers.
- **`tests/`** — 21 pytest checks: build integrity, page well-formedness and
  balanced tags, internal link resolution, checklist/worksheet/glossary
  content guarantees, converter unit tests, and privacy scans
  (no `<script>`, no `http(s)://` or `www.` anywhere, no secret patterns).
- **`README.md` / `LICENSE` / `.gitignore`** — README credits
  Asdale Dynamics, LLC and documents the privacy guarantees; LICENSE is MIT:
  *Copyright (c) 2026 Asdale Dynamics, LLC*.

## How to run it

```bash
python3 build.py              # build the site into site/
python3 build.py --check      # self-verify every page
python3 -m pytest tests/ -v   # run the full test suite
# then open site/index.html — double-click works, no server needed
```

## Verification results (final clean run, 2026-10-26)

- `python3 build.py` → "Built 12 pages + stylesheet into site/" (from scratch, no folder or stale files present)
- `python3 build.py --check` → "Check passed: 13 files, all local, all titled."
- `python3 -m pytest tests/` → **21 passed in 0.08 s**, run twice: once with
  `site/` present and once after `rm -rf site` to prove the suite builds
  everything itself
- Headless Chromium `--dump-dom` renders `checklist.html` cleanly (45
  empty checkboxes present), confirming real-browser openability
- Manual pass through all 11 markdown pages for plain-English tone and
  garbled-line cleanup

## Privacy guarantees (test-enforced)

- No `http://`, `https://`, or `www.` strings anywhere in built output
- No `<script>`, `<iframe>`, or `javascript:` in any page
- No accounts, analytics, cookies, or web fonts
- No secrets or personal data in source files (regex-scanned by tests);
  every date, name, and address in the docs is a bracketed placeholder

## Known gaps / future ideas

- Printing relies on the browser's own Ctrl+P; a dedicated
  headless print-to-PDF build step (like the sibling kits) could
  be added later.
- No user-fillable digital form yet: worksheet and checklist are
  hand-writing-first by design; an optional localStorage-flavored
  version (still offline) is a possible later edition.
- The glossary covers 19 terms; a deeper edition could add broker-vs-carrier
  complaint-path detail and state-by-state DMV timing tables.
- Utility scripts assume the common US case; municipal trash/water
  billing varies more than the guide implies (it warns, it doesn't list).
- No dark mode: the palette is paper-calm on purpose.
