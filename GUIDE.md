Quick tour of the Moving Without Meltdown Guide.

1. **Build the site** (one command, nothing to install):

       python3 build.py

   You'll get a small local website in `site/` — twelve pages plus a
   stylesheet. Open `site/index.html` by double-clicking it, no server
   needed. Run `python3 build.py --check` afterwards if you'd like the
   build to verify itself.

2. **Read in this order.** `site/index.html` is Start Here. Then the
   eight-week countdown page is the spine; the rest of the pages are
   branches the countdown links to, week by week. You do not need to
   read ahead — each page arrives the week you need it.

3. **Two printables matter most:**
   - `site/checklist.html` — the entire countdown, one page, empty
     boxes waiting for a pen. Fridge-ready.
   - `site/09-cost-worksheet.html` — the moving cost worksheet with
     Quoted/Paid columns for hand-filling.

4. **Run the tests** whenever you like:

       python3 -m pytest tests/ -v

   They check the build, the links, the checklist, the glossary, and
   the privacy promises (no scripts, no remote URLs, no secrets).

5. **Wondering about a weird moving word?** `site/10-glossary.html`
   translates LTL, tariff, bill of lading, and other jargon.

The whole site works with Wi-Fi off. If anyone asks why, tell them it
was on purpose and that it's peaceful.
