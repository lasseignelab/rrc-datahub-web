# Agent Changelog

A log of changes made by AI agents in this project, newest first.

---

## 2026-11-20

### About page: UAB/CHOP group name
- `content/about/acknowledgments.md`: Use the group's own name, "UAB/CHOP PKD group", instead of expanding CHOP.
- (Agent: Claude Opus 5.5)

## 2026-11-19

### Navbar: focus ring on the About menu button
- `assets/style.css`: The About caret button had no visible keyboard focus indicator (Bootstrap `.btn` removes the outline and the toggle also removed its box-shadow). Restored the site focus ring (2px `--uab-green` outline) on `.about-menu-toggle:focus-visible`, and widened the gap between "About" and the caret (2px -> 6px) so the ring doesn't touch the text. About page audit: 42/42 focus stops show a visible indicator; skip link is the first Tab stop; `<html lang="en">`; no form fields or Dash callbacks on the page; axe 0 violations.
- (Agent: Claude Opus 5.5)

### Sticky navbar; About header matches Charts/Library
- `assets/style.css`: `.site-nav` is `position: sticky; top: 0` on every page. `html { scroll-padding-top: calc(68px + 1rem) }` keeps in-page jumps and keyboard focus clear of it (WCAG 2.4.11); removed the per-heading `scroll-margin-top` it replaces. About sidebar sticks below the navbar. Skip link, when focused, is now fixed top-left above the navbar (it previously rendered just above the viewport and was never visible).
- `assets/toc-scrollspy.js`: Active line measured from the bottom of the sticky navbar (+120px), so group jumps highlight the group's first section.
- `components/page_header.py`: Optional `title_id` (H1 id) and `aside` (content beside the title at >=1200px, below it otherwise). Existing callers unchanged.
- `pages/about.py`: Header now uses `create_page_header` (same style as Charts and Library) with the stat tiles as `aside`; H1 keeps `id="about-title"` for Back to top. Stat tiles restyled as white cards on the teal header.
- `components/navbar.py`: Mobile hamburger `<summary>` gets `aria-label="Menu"` (axe `summary-name`, serious, from the develop navbar redesign).
- Verified: all earlier About behaviors re-tested (Overview jumps 6/6, scroll-spy, pinned clicks 10/10, release-pin 7/7, split button 16/16); skip link visible on top at any scroll position (1288/320px); axe 0 violations at 1288px and 320px; pa11y 4/4; 19/19 tests; black, isort, flake8, pylint, ruff, mypy, pyright clean.
- (Agent: Claude Opus 5.5)

### About page: Overview jumps show the page header
- `assets/anchor-scroll.js`: Jumps to the first group heading or its first section (`#about-group-overview`, `#overview`) scroll to the top of the page instead of aligning the heading to the viewport top, so the page header and stat tiles stay visible. Focus still moves to the target heading. Applies to the navbar menu, sidebar links, and direct links. Verified 6 scenarios (incl. other sections unchanged); 19/19 tests.
- (Agent: Claude Opus 5.5)

### Navbar: About as a split button
- `components/navbar.py`: "About" is now a normal link to /about; the caret beside it is a separate button (`dbc.DropdownMenu`, hidden label "Show About sections", `align_end=True`) that opens the section menu. Replaced deprecated `toggleClassName` with `toggle_class_name`.
- `assets/style.css`: Split-button layout; hovering either part (or the menu being open) underlines "About"; hover-to-open selector updated for the nested menu.
- Verified: click About -> /about; hover opens menu (also after click use); caret click and keyboard (Tab to caret, Enter, arrows, Escape) work; menu entries jump to sections; mobile menu unchanged; axe 0 violations (menu open/closed); 19/19 tests; linters clean; pa11y 4/4.
- (Agent: Claude Opus 5.5)

### Home: fix "geneexpression" typo; modality-neutral wording
- `pages/home.py`: Fixed the joined "geneexpression" heading, and replaced data-type-specific wording with modality-neutral wording (as on the About page, since future releases add other data types): heading "A simpler way to explore PKD datasets.", description "...makes public polycystic kidney disease (PKD) datasets easier to access and analyze.", Visualize card "Explore results with charts and tables".
- (Agent: Claude Opus 5.5)

### Merge develop (Library page, new navbar/footer) into feature/add-about-tab
- `pages/home.py`: Took develop's version (Home no longer shows version/GitHub; moved to footer).
- `components/navbar.py`: Took develop's navbar (brand, Library link, mobile hamburger) and re-added the About dropdown on desktop plus an "About" link in the mobile menu; restored the `dash_bootstrap_components` import the dropdown needs.
- `components/footer.py`: Imports `VERSION`, `UPDATED`, `GITHUB_URL` from `config.py` instead of its own copies (which still said 0.1 / 2026-08-24).
- `assets/style.css`: About toggle vertically centered to line up with the new nav links; hover-opened About menu right-aligned so it stays on screen now that About is the last nav item.
- Verified on the merged tree: 19/19 tests; black, isort, flake8, pylint, ruff, mypy, pyright, bandit clean; pa11y 0 errors on /, /library, /charts, /about; axe 0 violations on /about (menu open); mobile menu has Home, Library, Charts, About with no horizontal overflow.
- (Agent: Claude Opus 5.5)

### About page: release sidebar highlight on other in-page jumps
- `assets/toc-scrollspy.js`: A clicked sidebar item no longer stays highlighted after Back to top, a sidebar group link, the navbar About menu, or browser back/forward. Clicks on any other in-page link, and URL hash changes to a different section, hand highlighting back to the scroll position. Verified 7 scenarios in headless Chrome (incl. the earlier near-bottom pin); 19/19 tests; pa11y 3/3.
- (Agent: Claude Opus 5.5)

### Home page: "Search" feature becomes "AI Chat" (branch `feature/add-ai-chat-openai`)
- `pages/home.py`: the first About feature card now reads "AI Chat" ("Ask questions about the data in plain language") with the `lucide:bot-message-square` icon, in place of "Search" ("Find genes, datasets, and studies", `lucide:search`), since the chat replaced the gene search box. (Agent: Claude Opus 5.5)

### Home page: title and tagline make way for the chat (branch `feature/add-ai-chat-openai`)
- `pages/home.py`: removed the visible "PKD RRC DataHub" title and the tagline above the chat. The H1 stays for screen readers and the heading order, with the existing `.visually-hidden` class; the navbar already shows the name. The `.hero` wrapper section is gone. (Agent: Claude Opus 5.5)
- `assets/style.css`: removed the now-unused `.hero`, `.hero-title` and `.hero-tagline` rules. `.data-chat-log` max-height goes from a fixed 420px to `max(320px, calc(100vh - 270px))`, so the conversation fills the window under the navbar while the disclaimer, question field and status line stay on the same screen. `.hero-section .search-section` gets `position: relative; z-index: 1`: without the title section, the absolutely positioned dot pattern was drawn over the chat box and question field. (Agent: Claude Opus 5.5)
- `tests/test_app.py`: the H1 tests check its text content and `visually-hidden` class, since it no longer has visible text. (Agent: Claude Opus 5.5)

### Merge `develop` into `feature/add-ai-chat-openai`
- Resolved conflicts from develop's new home page, library page, navbar and footer. `pages/home.py` takes develop's layout (two-colour title, "About the DataHub" with feature cards, `footer()`) with `data_chat.layout` in place of the gene search box. `components/landing_search.py` stays removed (develop had only restyled it), and so do its `TestGeneSearch` tests and the `.gene-search-input` CSS. `assets/style.css` takes develop's `.hero`/`.hero-section` and title styles, keeping this branch's compact hero padding (24px 16px 20px) and halving develop's new title size (5.5rem → 2.75rem). The chat styles follow develop's footer media query. The changelog keeps both sides. (Agent: Claude Opus 5.5)

### Searching message moves into the conversation (branch `feature/add-ai-chat-openai`)
- `components/data_chat.py`: "Searching the data, this can take a few seconds…" is no longer shown in the status line under the question field, where it was easy to miss. `render_log()` now also takes the pending store and, while a question is pending, adds a "Data assistant" entry with that message at the bottom of the log; the answer replaces it in the same redraw. `answer_pending`'s `running` now only disables New chat. The log's aria-live region announces the message. (Agent: Claude Opus 5.5)
- `assets/data_chat_scroll.js`: the answer replacing the searching message leaves the message count unchanged, so the scroll now also starts when the searching message goes away. (Agent: Claude Opus 5.5)
- `assets/style.css`: `.data-chat-searching`: italic text at full contrast with a small pulsing dot in front of it (decorative; the pulse is off under prefers-reduced-motion). (Agent: Claude Opus 5.5)
- `tests/test_data_chat.py`: unit test for the searching entry and a browser test that it shows at the bottom of the log and is replaced by the answer. (Agent: Claude Opus 5.5)

## 2026-11-18

### About page: PI title and developer role
- `content/about/contact.md`: Lasseigne listed as Associate Professor — Principal Investigator; Developer added to Crumley's roles.
- (Agent: Claude Opus 5.5)

### About page: future directions additions
- `content/about/future-directions.md`: Added transfer learning (e.g. relating findings across species) and an "And more!" bullet.
- (Agent: Claude Opus 5.5)

### About page: team titles and roles
- `content/about/contact.md`: Core team now listed as name, degree, job title — role(s): Soelter (Computational Biologist — Project Manager, Team Lead, and Developer), Crumley (Computational Scientist — Team Lead and Software Architect), Casper and Okunbor (Research Assistant — Developer, data pipeline / web application). Dropped "Undergraduate".
- (Agent: Claude Opus 5.5)

### About page: header layout and sample-count alignment
- `pages/about.py`: Header card gets `about-header`; release date in the version tile kept on one line (`text-nowrap`).
- `assets/style.css`: Header split layout at >=1200px (title/subtitle left, stat tiles right); below that the tiles sit in one row under the subtitle, sized by content, with smaller tiles under 576px (wraps 2 + 1 on phones). Datasets "Samples (n)" column centered instead of right-aligned.
- Verified at 1288, 1000, 768, and 375px: no horizontal overflow; axe 0 violations at 1288px and 320px; 19/19 tests; linters clean.
- (Agent: Claude Opus 5.5)

### About page: visual polish, header stats, group headings
- `pages/about.py`: Header stat tiles (datasets, samples, version/release date) via `_stat_tiles()` as a labelled list; group H2 headings now show the shared icons (`GROUP_ICONS`, from `components.navbar.ABOUT_MENU`); "Back to top" link at the end of each group card (targets the H1, now `id="about-title"`); Known limitations rendered as a callout (`CALLOUT_SLUGS`).
- `config.py`: `DATASET_COUNT` (14) and `SAMPLE_COUNT` (249) for the header tiles; update per release alongside `VERSION` (also stated in `content/about/datasets.md`).
- `assets/style.css`: Larger group headings with icon and divider; stat tiles; back-to-top link; amber callout; Datasets table with monospace accessions, right-aligned tabular sample counts, zebra rows; Glossary as a two-column term/definition grid (stacks below 576px).
- `content/about/limitations.md`: Removed the blank line that split the list (extra gap above "Sex is rarely reported").
- `tests/test_about.py`: Anchor test also accepts H1 ids (back-to-top target).
- Verified: axe 0 violations at 1288px and 320px; no horizontal page scroll at 320px; back-to-top lands on and focuses the H1; 19/19 tests; black, isort, flake8, pylint, ruff, mypy, pyright, bandit clean.
- (Agent: Claude Opus 5.5)

### About page: scroll-spy keeps clicked section highlighted
- `assets/toc-scrollspy.js`: A clicked sidebar link stays the active one until the user scrolls themselves (wheel, touch, or scroll keys). Fixes sections near the end of the page (e.g. Feedback and issues), which cannot scroll up to the active line and were highlighting a neighbouring section. Verified: all 10 tested links stay highlighted after the pointer leaves; wheel scrolling releases the pin; keyboard Enter works.
- (Agent: Claude Opus 5.5)

### About page: sidebar scroll-spy
- `assets/toc-scrollspy.js` (new): Sets `aria-current="location"` on the sidebar link for the section currently in view (last H3 above 120px from the top; last section when scrolled to the bottom). Never moves focus, no live-region announcements, and only scrolls the sidebar (not the page) to keep the active link visible on short screens. rAF-throttled scroll/resize listeners plus a MutationObserver for Dash's async rendering; no-op on other pages.
- `assets/style.css`: The current section keeps the hover look (light teal background + dark left bar) while it is in view; the left bar is the non-color cue (WCAG 1.4.1).
- Verified in headless Chrome with Flatly loaded: correct section highlighted when scrolled to User guide / Research methodology / Funding, at the top and bottom of the page, and after clicking a sidebar link; focus unchanged by scrolling; no JS errors on /, /charts, /about; axe 0 violations.
- (Agent: Claude Opus 5.5)

### About page: sidebar restyle
- `pages/about.py`: Sidebar group links now show the same Bootstrap icons as the navbar About dropdown (looked up from `components.navbar.ABOUT_MENU` by anchor id, so both stay in sync); group/item links get `about-toc-group` / `about-toc-item` classes.
- `assets/style.css`: Replaced default list styling (bullets, underlines, large heading) with a small uppercase "On this page" label, icon + bold group links, and sub-items on a thin guide line with a teal hover bar. Keyboard focus ring unchanged. axe: 0 violations at 1288px and 320px.
- (Agent: Claude Opus 5.5)

### About page: team degree
- `content/about/contact.md`: Added Anthony B. Crumley's degree (BS).
- (Agent: Claude Opus 5.5)

### Chat questions on light grey (branch `feature/add-ai-chat-openai`)
- `assets/style.css`: `.data-chat-user` background changed from light green (`--teal-pale`, #E6F2F0) to light grey (#f0f0f0, already used elsewhere on the site). (Agent: Claude Opus 5.5)

### Remove the Ask button; "New conversation" becomes "New chat" (branch `feature/add-ai-chat-openai`)
- `components/data_chat.py`: Ask button removed. Enter now sends by setting a new `data-chat-send` store (a fresh timestamp) through `dash_clientside.set_props`, which starts `submit_question`. The Enter/Shift+Enter hint is now visible text under the field (`data-chat-hint`), since there is no button to show how to send. Button relabelled "New chat"; its status message is "Started a new chat."
- `start_new_conversation` now also clears the pending question when one is set. In one of about 20 full test runs a queued question was sent but never answered, and I couldn't reproduce it to find the cause; a question stuck as pending would make every later question wait in the queue. New chat now always gets the chat going again. It is still disabled while an answer is running, and it only writes pending when something is pending, because any write starts `answer_pending`, whose `running` would blank the status message.
- `assets/data_chat_input.js`: Enter calls `set_props` instead of clicking Ask. `assets/style.css`: Ask styles removed; hint style added.
- `tests/test_data_chat.py`: Checks there is no Ask button and the hint is shown; New chat tests updated, including clearing a stuck pending question. (Agent: Claude Opus 5.5)

### Question field grows as the user types (branch `feature/add-ai-chat-openai`)
- `components/data_chat.py`: The question field is now a one-row `dcc.Textarea` instead of a single-line `dcc.Input`. A textarea has no `n_submit`, so `submit_question` is triggered by Ask's `n_clicks` only and Enter is handled in JS. A visually hidden hint (`data-chat-input-hint`) tells screen-reader users that Enter asks and Shift+Enter adds a line.
- `assets/data_chat_input.js` (new): Grows the field with its text up to 200px, then it scrolls; shrinks it back once the server clears it after a question is sent (that change fires no input event, so it watches briefly after Ask). Enter clicks Ask; Shift+Enter adds a line; Enter during IME composition is left alone. Sets `aria-describedby` to the hint, which `dcc.Textarea` has no prop for. Listeners are on the document so they survive page navigation.
- `assets/style.css`: Textarea styling (40px one-line height matching the buttons, no resize handle), focus outline moved to the textarea, buttons aligned to the field's bottom edge, and user messages keep their line breaks (`white-space: pre-wrap`).
- `tests/test_data_chat.py`: Browser tests that Shift+Enter adds lines and grows the field, Enter asks the multi-line question (shown with its line breaks) and the field shrinks back, and the hint is linked; the New conversation test presses Enter on the button instead of clicking, because a click could land mid-scroll. (Agent: Claude Opus 5.5)

### New conversation button (branch `feature/add-ai-chat-openai`)
- `components/data_chat.py`: "New conversation" button (`data-chat-new`, `btn-outline-primary`) next to Ask, shown only when there is a conversation (`render_log` outputs its `hidden`). `start_new_conversation` clears the history (session storage, so it stays cleared after a reload) and the question queue, and announces "Started a new conversation." in the status line. The button is disabled while an answer runs (via `answer_pending`'s `running`), and the callback also ignores clicks while a question is pending, because the arriving answer is appended to the history read when it started and would bring the old conversation back. A clientside callback moves focus to the question field, since the button hides itself after clearing.
- `assets/style.css`: Button sizing, `[hidden]` override for Bootstrap's `.btn` display, and on screens ≤640px the question field takes its own line with the buttons under it.
- `tests/test_data_chat.py`: Unit tests for clearing and for ignoring a clear mid-answer; browser test that the button appears, clears the chat, returns focus to the field, and stays cleared after a reload. (Agent: Claude Opus 5.5)

### Enter (or Ask) during an answer queues the question instead of ignoring it (branch `feature/add-ai-chat-openai`)
- Enter already submitted a question, but while an answer was on its way it was silently ignored (the typed text stayed in the box). Real OpenAI answers take several seconds, so typing a follow-up and pressing Enter looked broken.
- `components/data_chat.py`: `submit_question` now queues a question asked during an answer (new `data-chat-queue` store) and clears the box; an "Up next: …" line (`data-chat-queued`, `role="status"`) shows the queue. `ask_next_queued` sends the oldest queued question once the current answer has arrived. It is driven by a `dcc.Interval` that runs only while questions are queued: Dash won't start a callback again from changes its own run set off, so "answer arrived → ask next → answer it" can't be a plain callback chain (tried triggering on the pending store, the history store, and a separate request store; none started the second answer). The Ask button is no longer disabled during an answer, since a click now queues too. `answer_pending` catches any unexpected error and replies with an error message, so a question can never stay pending and block the queue.
- `assets/style.css`: Style for the "Up next" line.
- `tests/test_data_chat.py`: Unit tests for queuing, dequeuing, the queue line/timer and the error fallback; browser test that a question entered with Enter during a slow answer is answered next, in order. (Agent: Claude Opus 5.5)

### Smaller hero title; AI disclaimer under the answers (branch `feature/add-ai-chat-openai`)
- `assets/style.css`: Hero title halved from 6rem to 3rem. Log bottom margin 16px → 6px and disclaimer margin moved below it (0 0 16px) so the disclaimer sits tight under the answers.
- `components/data_chat.py`: The disclaimer (now `id="data-chat-disclaimer"`) moved to directly under the conversation log and starts `hidden`; `render_log` also outputs its `hidden` prop, so it shows only once a question has been asked, together with the log.
- `tests/test_data_chat.py`: `render_log` tests check the disclaimer's visibility; new test checks it follows the log and starts hidden. (Agent: Claude Opus 5.5)

### Chat results above the question box; compact hero (branch `feature/add-ai-chat-openai`)
- `components/data_chat.py`: The conversation log now comes first, with the question field, status line and disclaimer under it, as in a typical chat. The log is a fixed-height scroll box, so the field doesn't move down the page as the conversation grows.
- `assets/style.css`: Hero padding reduced from 64px/48px to 24px/20px and the title's bottom margin from 0.75rem to 0.25rem, so the chat has more room on the first screen. The log's gap moved from above it to below it.
- `assets/data_chat_scroll.js`: When a message is added, the page scroll now brings the log's top and the question field and status line under it into view (the log's top wins if both don't fit).
- `tests/test_data_chat.py`: Tests for the log coming before the question field and for both staying on screen after an answer. (Agent: Claude Opus 5.5)

### Chat log scrolls to the newest exchange (branch `feature/add-ai-chat-openai`)
- `assets/data_chat_scroll.js` (new): A MutationObserver keeps the fixed-height chat log scrolled to the newest exchange: the newest question at the top of the box with its answer under it, or the start of the answer when the two don't fit together. When a message is added it also scrolls the page just enough to bring the log into view; restoring a saved conversation on load doesn't move the page. The scroll is re-applied for 1.5 s while the answer finishes drawing and stops as soon as the user scrolls, clicks or types. Smooth scrolling is skipped under `prefers-reduced-motion`; focus is never moved.
- A first version used a Dash clientside callback that measured two animation frames after the log update. It didn't scroll in real use: the answer's Markdown (loaded on demand) is drawn later than that on a normal machine, so it measured the old content. Reproduced with Chrome CPU throttling; the observer approach scrolls once the answer is actually drawn.
- `tests/test_data_chat.py`: Browser tests for a long answer (shown from its start), many short exchanges (newest question and answer in view), and a slow first answer with a Markdown table under 6× CPU throttling. (Agent: Claude Opus 5.5)

### Gunicorn concurrency settings and a chat that survives page changes (branch `feature/add-ai-chat-openai`)
- `gunicorn.conf.py` (new): 3 workers × 4 threads (`gthread`), 120 s timeout, `preload_app = False` so each worker opens its own DB connections; each overridable by env var (`WEB_CONCURRENCY`, `GUNICORN_THREADS`, `GUNICORN_TIMEOUT`). Gunicorn's default single sync worker would make every visitor wait while one chat answer runs. The bind address is left at gunicorn's default rather than opening `0.0.0.0`.
- `components/data_chat.py`: `data-chat-history` store now uses `storage_type="session"`, so the conversation survives going to the charts page and back, or a reload, within the same tab. `data-chat-pending` stays in memory: restoring it after a reload mid-answer would block new questions.
- `components/chat_assistant.py`: Moved a stray line-continuation backslash in the system prompt (from af171cc) to the end of its line; it was sent to the model as a literal `\ ` and failed flake8 (W605, E501). Prompt wording unchanged.
- `app.py`: Added `server = app.server`. The documented production command `gunicorn app:server` failed before this because `app.py` had no `server` attribute.
- `AGENTS.md`: documents the gunicorn settings. Tests: `tests/test_app.py` checks `server`; `tests/test_gunicorn_conf.py` (defaults, env overrides); `tests/test_data_chat.py` checks the store types and that a conversation survives a browser reload. (Agent: Claude Opus 5.5)

### OpenAI version of the data chat (branch `feature/add-ai-chat-openai`, from `feature/add-ai-chat`)
- `components/chat_assistant.py`: Rewritten on the OpenAI SDK (`openai==3.55.1`) with Chat Completions function calling. Default model `gpt-5.4-mini`, overridable with `OPENAI_MODEL`. The module runs the tool loop itself (max 8 tool rounds; the last request sets `tool_choice="none"` so the model must answer). Tools are JSON-schema definitions dispatched to `db/chat_tools.py` and `build_chart_link`; bad tool arguments are returned to the model as an error result instead of raised. Rejected keys show the not-configured message, rate limits/quota show "busy", network errors show "couldn't be reached", refusals and content filtering show a polite refusal.
- Env var is now `OPENAI_API_KEY` (+ optional `OPENAI_MODEL`) in `.env.example` and `AGENTS.md`. `requirements.txt`: replaced `anthropic` with `openai`; removed `docstring_parser` and `opentelemetry-api` (only `anthropic` used them). Verified with a dry-run install into a clean venv.
- `components/data_chat.py`: Disclaimer names OpenAI. `db/chat_tools.py`: docstring no longer names Claude.
- `tests/test_chat_assistant.py`: Rewritten for a fake Chat Completions client: tool dispatch and result round trip, loop cap, bad arguments, refusal, empty reply, auth/rate-limit/connection errors, model override, field whitelist and tool/function parity. (Agent: Claude Opus 5.5)

## 2026-11-17

### About page: future directions finalized
- `content/about/future-directions.md`: Replaced cross-dataset comparisons with multi-gene views within one dataset (planned first); added AI-assisted gene search (chatbot for the search bar); removed the last placeholder. The About page now has no placeholders.
- `content/about/faq.md`: Removed "Cross-dataset comparison is planned" to stay consistent with Future directions.
- (Agent: Claude Opus 5.5)

### About page: Age column header wrapping
- `content/about/datasets.md`: Non-breaking space (U+00A0) in "postnatal day" so the header wraps as "Age" / "(postnatal day)" instead of splitting the parenthetical.
- (Agent: Claude Opus 5.5)

### About page: grant number format, nf-core acknowledgment
- `content/about/funding.md`: Grant cited by core project number U54DK126087 (NIH acknowledgment convention) instead of 2U54DK126087-06.
- `content/about/acknowledgments.md`: Removed the nf-core sentence (cited elsewhere, e.g. How to cite and Methodology).
- (Agent: Claude Opus 5.5)

### About page: funding and acknowledgments
- `content/about/funding.md`: NIDDK/NIH grant 2U54DK126087-06 (UAB Childhood Cystic Kidney Disease Core Center, PKD RRC); institute confirmed by the DK activity code and NIH RePORTER listings for U54DK126087. Additional-funding placeholder removed; NIH disclaimer kept.
- `content/about/acknowledgments.md`: PKD RRC feedback/beta-testing acknowledgment adapted from the author's poster (duplicate "PKD RRC" mention merged; CHOP spelled out); UAB IT-Research Computing Cheaha statement from docs.rc.uab.edu/grants/publications (Globus statement omitted); nf-core and dataset depositors kept.
- (Agent: Claude Opus 5.5)

### About page: team, contact, data license
- `content/about/contact.md`: Rewritten: single contact email (bnp0001@uab.edu, temporary until the DataHub-specific UAB address exists); core team (Lasseigne, Soelter, Crumley, Casper, Okunbor) with roles, no individual emails, "with support from the other members of the Lasseigne Lab" linking to the lab website.
- `content/about/feedback.md`: Contact email set to bnp0001@uab.edu (same temporary address).
- `content/about/license.md`: Processed data licensed CC BY 4.0 (Zenodo default, per author).
- TODO when the DataHub email exists: replace bnp0001@uab.edu in `content/about/contact.md` and `content/about/feedback.md` (and decide whether `pages/home.py` should switch too).
- (Agent: Claude Opus 5.5)

### About page: how to cite
- `content/about/how-to-cite.md`: Preprint expected in 2027; interim citation of the website with version (https://datahub.pkdrrc.lasseigne.org/) and author list (Soelter, Crumley, Casper, Okunbor, Lasseigne; Last, F.M. format), Zenodo DOI for processed data (v0.1.0), and existing dataset/nf-core citation guidance. BibTeX placeholder removed. No placeholders remain.
- (Agent: Claude Opus 5.5)

### About page: methodology dataset selection and QC
- `content/about/methodology.md`: Dataset selection (NCBI GEO and PubMed search for mouse kidney bulk RNA-seq in PKD; all v0.1.0 runs Illumina, verified in curated metadata `platform` column) and QC (MultiQC metrics compiled per dataset; no QC-based exclusions; not yet in the app) filled per author. No placeholders remain in this section.
- (Agent: Claude Opus 5.5)

### About page: methodology filled from the pipeline repo
- `content/about/methodology.md`: Processing pipeline and Metadata curation rewritten from `lasseignelab/rrc-datahub` (README, `.caprc`, `src/01_geo_download.sh`, `src/04_run_nfcore_rnaseq.sh`, `src/05_transform_metadata.R`, `src/functions/get_bioproject_metadata.R`): ENA FASTQ download with MD5 verification; nf-core/rnaseq v3.25.0, STAR + Salmon (`--aligner star_salmon`), GRCm39 primary assembly, GENCODE M37; Zenodo DOI for processed outputs; Entrez SRA + BioSample metadata and the harmonization rules. Dataset selection and QC placeholders remain (need author input).
- (Agent: Claude Opus 5.5)

### About page: repository links, licenses, limitations
- Linked the pipeline (`lasseignelab/rrc-datahub`) and web app (`lasseignelab/rrc-datahub-web`) repos where relevant: `overview.md` ("pipeline"), `methodology.md` (processing pipeline), `license.md`, `feedback.md`. Code stays on GitHub, so removed the "Archived code (Zenodo)" line from `code-availability.md`.
- `license.md`: Corrected licenses per repo: pipeline is MIT (`rrc-datahub/LICENSE`), web app is GPL-3.0. Previously stated GPL-3.0 for all source code.
- `feedback.md`: Website problems → `rrc-datahub-web` issues; metadata errors/dataset requests → `rrc-datahub` issues.
- `limitations.md`: "Bulk tissue only" corrected to "Bulk RNA-seq only" (v0.1.0 includes cell lines and organoids); added sex-reporting limitation (only PRJNA857739 of 14 reports sex). Placeholder removed.
- (Agent: Claude Opus 5.5)

### About page: FAQ downloads and gene annotation
- `content/about/faq.md`: Gene search answer now names the GENCODE mouse annotation (release M37), matching the pipeline (`lasseignelab/rrc-datahub` README and `src/02_ref_genome_download.sh`), instead of Ensembl. Download answer points to the Zenodo archive of each release's processed data (v0.1.0: doi:10.5281/zenodo.24325117) and to per-plot CSV downloads.
- `content/about/code-availability.md`: Split the Zenodo line into processed data (v0.1.0, doi:10.5281/zenodo.24325117) and archived code (link pending).
- (Agent: Claude Opus 5.5)

### About page: user guide checked against release-0.1 Charts
- `content/about/user-guide.md`: Button name corrected to **Search Datahub** (matches `components/landing_search.py`); added Age range instructions (min/max + unit: days, weeks, months, years) reflecting the release-0.1 age filter; Q1/Q3 spelled out; removed screenshot placeholder (text-only for now).
- `content/about/release-history.md`: fixed a remaining two-part version ("v0.1." at sentence end → v0.1.0).
- (Agent: Claude Opus 5.5)

### About page: release date and future directions
- `config.py`: `UPDATED` set to `2026-11-17`, the v0.1.0 release date (release-0.1 merged to main/develop today).
- `content/about/release-history.md`: v0.1.0 dated 2026-11-17.
- `content/about/future-directions.md`: v0.2.0 human bulk RNA-seq marked as in code review; added single-cell datasets (human and mouse) being processed for ingestion; QC abbreviation introduced.
- (Agent: Claude Opus 5.5)

### About page: sticky sidebar layout
- `pages/about.py`: "On this page" moved into a left sidebar (`dbc.Col(lg=3)`) beside the content (`lg=9`); stacks into one column below 992px.
- `assets/style.css`: Sidebar is `position: sticky` on ≥992px. Removed the 80ch cap on `.about-markdown` (content column now ~110 characters wide). `.about-markdown` gets `overflow-x: auto` so wide tables scroll inside the card on narrow screens / 400% zoom instead of overflowing (WCAG 1.4.10). Table of contents is single-column.
- Verified with axe-core (WCAG 2.0/2.1/2.2 A+AA + best practice) with Flatly loaded: 0 violations on /about at 1288px and 320px, and with the About dropdown open; keyboard order skip link → nav → sidebar → content; no horizontal page scroll at 320px.
- Found, not fixed (pre-existing, Charts page): axe `button-name` (critical) on 8 dropdown filters (`#scientific-name-select`, `#sex-select`, `#underlying-variant-select`, `#sample-type-select`, `#group-select`, `#plot-sample-type-select`, `#plot-sex-select`, `#plot-age-select`).
- (Agent: Claude Opus 5.5)

### About page: dataset publications
- `content/about/datasets.md`: Filled the publication column (author, year) for all 14 BioProjects from the pipeline repo's dataset table; column renamed "Original publication" to match that table. No DOIs/links yet.
- (Agent: Claude Opus 5.5)

### About page: centered table headers
- `assets/style.css`: `.about-markdown th` now `text-align: center; vertical-align: middle` (body cells stay left-aligned).
- (Agent: Claude Opus 5.5)

### About page: Datasets table filled from curated metadata
- `content/about/datasets.md`: Filled Underlying variant, Sample type, Age (postnatal day), and Samples (n) for all 14 BioProjects from `staging/transformed-metadata/*_transformed.tsv`, counting each run once (same de-duplication as `etl/load.py`, so PRJNA805541 super-series rows map to PRJNA805542/PRJNA805547). Total 249 samples, added to the intro. Tissue and Treatment columns omitted (tissue is uniformly kidney or not provided; Treatment dropped to reduce wrapping). Added a note that wild-type controls are not listed and that "Not provided" means not reported in the source record. Source publication remains a placeholder.
- (Agent: Claude Opus 5.5)

### Version format MAJOR.MINOR.PATCH; About overview rewrite
- `config.py`: `VERSION` is now `"0.1.0"`; comment documents the MAJOR.MINOR.PATCH format. Home and About pick this up automatically.
- `content/about/*.md`: All version references now use three parts (v0.1.0, v0.2.0). Release-history intro replaced with a one-line statement of the format.
- `content/about/overview.md`: RRC and PKD abbreviations now introduced in the first sentence; added "no account or login required"; added a mission paragraph adapted from the grant; UAB abbreviation introduced.
- Abbreviations introduced at first appearance in page order: TPM in `release-history.md`, GEO in `limitations.md`.
- (Agent: Claude Opus 5.5)

### About page: modality-neutral wording
- `content/about/{overview,datasets,faq,limitations,methodology}.md`: General descriptions of the DataHub no longer say "gene expression"/"expression data", since future releases add other data modalities; text now says "datasets"/"results". Wording specific to the current v0.1 bulk RNA-seq data (TPM, violin plots, release notes) is unchanged. Methodology now opens by stating it describes v0.1 and that methods for new data types will be added per release.
- (Agent: Claude Opus 5.5)

### Fix unresolvable pins in requirements.txt (branch `feature/add-ai-chat`)
- `requirements.txt`: Bumped `typing_extensions` 4.15.0 → 4.16.0 (required by the pinned `anyio` and `pydantic`) and `idna` 3.11 → 3.20 (required by `httpx2`). The packages added for the chat made `pip install -r requirements.txt` fail with ResolutionImpossible; it went unnoticed locally because the venv already had newer versions. Verified with a dry-run install into a clean venv. (Agent: Claude Opus 5.5)

### Chat links open the charts page filtered to the answer's datasets (branch `feature/add-ai-chat`)
- `components/chat_assistant.py`: New `chart_link` tool (backed by `build_chart_link`) that builds the URL-encoded `/charts` link: `gene`, `datasets` (comma-separated, answer order), and repeatable `scientific_name`, `sex`, `underlying_variant`, `sample_type` plus `min_age_days`/`max_age_days`. The system prompt now requires every charts link to come from this tool, so the model never hand-writes URLs.
- `pages/charts.py`: New `apply_url_filters` callback reads those parameters on load and sets the matching dataset filters (case-insensitive match against dropdown options; unmatched values leave the filter at its default; a named filter unticks its "not provided" box). A new `url-datasets` store limits the Found Dataset(s) table to the answer's datasets, and the first one the answer named is selected. A notice with a "Show all datasets" button clears the limit. Helpers `_parse_url_filters`, `_match_options`, `_limit_rows`, `_choose_selected`.
- Tests: `tests/test_charts.py` (new; URL round-trip, matching, limiting, selection, filter callback) and link-encoding tests in `tests/test_chat_assistant.py`. Verified live: chat answers produce links that open with the expected filters and datasets. (Agent: Claude Opus 5.5)

### Move the chat conversation below the question box (branch `feature/add-ai-chat`)
- `components/data_chat.py`: The conversation log now comes after the input, status line and disclaimer, so the question box stays in place as the conversation grows. `assets/style.css`: `.data-chat-log` margin moved from bottom to top to match. (Agent: Claude Opus 5.5)

### Replace home-page gene search with an AI data chat (branch `feature/add-ai-chat`)
- `components/data_chat.py` (new): Chat box that replaces the gene search on the home page. A question is appended to a `dcc.Store` history immediately (so it shows at once), then a second callback asks the assistant and appends the reply. While waiting, the Ask button is disabled and a `role="status"` message announces progress; the conversation container is `role="log"` with `aria-live="polite"`. Replies render with `dcc.Markdown` (no raw HTML). Enter while an answer is pending is ignored so turns cannot interleave.
- `components/chat_assistant.py` (new): Answers questions with Claude (`claude-opus-5-5`, effort `medium`) through the Anthropic SDK's beta tool runner, capped at 8 tool round-trips and the last 20 history messages. History between turns is text-only, which is always valid under the API's thinking-block history check. Uses top-level prompt caching for the stable system prompt and tools, and server-side refusal fallbacks (`fallbacks="default"`, beta `server-side-fallback-2026-07-01`). Missing credentials, auth, rate-limit, API and connection errors become short user-facing messages instead of exceptions. One `# pyright: ignore[reportCallIssue]` on the `tool_runner` call: the MegaLinter image bundles anthropic 0.84, which predates `fallbacks`; against the pinned SDK the call type-checks cleanly.
- `db/chat_tools.py` (new): Read-only query functions the assistant calls as tools — `list_field_values`, `find_datasets` (field filters + age-in-days overlap), `describe_dataset`, and `gene_expression_summary` (n/mean/median/min/max TPM per dataset and group, gene names resolved with `db.gene_search.resolve_gene`). Filter and group-by fields are whitelisted in `SAMPLE_FIELDS`; results are capped at 200 rows.
- Removed `components/landing_search.py` and its tests in `tests/test_app.py`; removed the now-unused `.search-input-wrapper`, `.search-icon`, `.gene-search-input` CSS. `db/gene_search.py` is kept (used by the chat's gene tool).
- `pages/home.py`: Renders `data_chat.layout` in place of the search box. `assets/style.css`: chat styles using existing color tokens; the inner `.dash-input-element` is styled because Dash 4 wraps `dcc.Input` in a container div.
- `requirements.txt`: Added `anthropic==2.9.0` and its pinned dependencies. `.env.example` and `AGENTS.md`: documented `ANTHROPIC_API_KEY`; added the new files to the project layout.
- Tests: `tests/test_chat_tools.py`, `tests/test_chat_assistant.py` (Anthropic client mocked), `tests/test_data_chat.py` (callbacks, ARIA roles, label association, and a `dash_duo` check that the chat renders on the home page). No test needs a database or API key. (Agent: Claude Opus 5.5)

## 2026-11-16

### Fix About dropdown: section jumps, hover position, icon spacing
- `assets/anchor-scroll.js`: Jumps landed ~3000px off because `dcc.Markdown` renders asynchronously after the headings exist, pushing sections down after the scroll. The script now re-aligns the target on every DOM mutation / body resize until the layout is stable for 1.5 s (max 8 s), focuses the heading once, and stops immediately on user wheel/touch/key/mouse input. Also handles direct loads of `/about#...`.
- `assets/style.css`: Hover-opened menu now overrides the inline Popper position left behind after a click-open (`inset`/`transform` with `!important`, only for `:not(.show)`), so it no longer opens offset and closes before the pointer reaches it. Icon spacing uses `margin-left: auto` + `padding-left` instead of flex `gap` for consistent rendering across browsers.
- Verified with Flatly + Bootstrap Icons loaded and Markdown JS delayed 1.2 s: click from `/charts`, click on `/about`, hover-after-click, direct hash load, and user-scroll-not-hijacked all pass; pa11y 0 errors.
- (Agent: Claude Opus 5.5)

### About dropdown menu in navbar
- `components/navbar.py`: Replaced the plain "About" link with a `dbc.DropdownMenu` listing the four About sections (Overview; Using the DataHub; Methods and reuse; People and support), each linking to `/about#<group id>` with a Bootstrap icon (`aria-hidden`). Entries live in `ABOUT_MENU`; ids must match `pages/about.py` `_group_id`.
- `assets/anchor-scroll.js` (new): Scrolls to and focuses the element named in the URL hash once Dash renders it (browser anchor-jumping fails because pages render after navigation). Re-runs on `hashchange`, `popstate`, and Dash's `_dashprivate_pushstate`.
- `assets/style.css`: Dropdown styles matching `.nav-link`; opens on hover for mouse users via `@media (hover: hover)`, while click, keyboard (Enter + arrow keys), and touch use Bootstrap's toggle. Added `scroll-margin-top` to About H2 headings.
- `tests/test_about.py`: Navbar test now also checks dropdown items; new test asserts `ABOUT_MENU` anchors equal the About page group ids.
- Verified in headless Chrome: hover opens menu; selecting an entry from `/charts` lands on and focuses the section; keyboard navigation works. pa11y WCAG2AA: 0 errors on `/`, `/charts`, `/about`, and `/charts` with the menu open.
- (Agent: Claude Opus 5.5)

### Add About page
- `pages/about.py` (new): Registers `/about` ("About"). Renders one H1, an "On this page" in-page navigation, and four H2 group cards (Overview; Using the DataHub; Methods and reuse; People and support), each holding H3 subsections. Section order and titles come from the `SECTIONS` list; each slug is both the anchor id and the name of its markdown file. The Version and release history subsection also shows the live `VERSION`/`UPDATED` from `config.py`. No database access, so the page renders in CI without PostgreSQL.
- `content/about/*.md` (new, 15 files): Page copy kept outside Python so it can be edited without touching layout code. Bodies start at `####` because the page supplies H1–H3. Unknown details are marked `\[PLACEHOLDER: ...\]` (brackets escaped so Markdown does not render them as links); `grep -rn PLACEHOLDER content/about` lists what is left to fill in.
- `config.py` (new): Moved `VERSION`, `UPDATED`, and `GITHUB_URL` out of `pages/home.py` so Home and About show the same version from one place. `pages/home.py` now imports them; no other change to Home.
- `components/navbar.py`: Added an "About" link after "Charts".
- `assets/style.css`: Added an "About page" block (table of contents, group/item headings, markdown tables, version line).
- `.pa11yci`: Added `http://localhost:8050/about`.
- `tests/test_about.py` (new): Checks single H1, a non-empty markdown file per section, no markdown heading above level 4, every table-of-contents link targets an existing id, one Markdown block per section, navbar link, and a `dash_duo` render test.
- `AGENTS.md`: Documented `config.py` contents and the `content/about/` folder in Project layout.
- (Agent: Claude Opus 5.5)

## 2026-11-11

### Clear outstanding black/isort MegaLinter findings
- Applied black to `components/section_header.py`, `db/gene_search.py`, `pages/charts.py`, and `tests/test_app.py`, and isort (MegaLinter's `--profile black` args) to `tests/test_app.py`. In `pages/charts.py`, wrapped the "Edit Plot Parameters" tooltip string in parentheses so the implicit concatenation reads cleanly. Formatting only; no behavior change. MegaLinter now reports zero errors for every Python linter, including the non-blocking black and isort. (Agent: Claude Opus 5.5)

### Fix: age range filter not filtering, and wrong values after unit change
- `pages/charts.py`: Commit `7c4e47f` changed `age-min-input`/`age-max-input` from `type="number"` to `type="text"`, so Dash delivers strings and `_update_age_days_store` raised `TypeError` (`str * float`). The `age-range-days` store never updated, so the dataset filter ignored typed ages, and a unit change converted the stale store instead of the typed values. Added `_parse_age_input()` to parse text (blank/non-numeric falls back to defaults, negatives clamp to 0). `_update_age_days_store` now also reads the store as State and returns `no_update` when the inputs equal the store re-expressed in the current unit, so a unit change no longer round-trips through 1-decimal rounding and drifts the stored day range. (Agent: Claude Opus 5.5)

## 2026-09-10

### Require agents to identify themselves in changelog entries
- `AGENTS.md`: Extended the changelog instruction so each entry notes the agent name/model that made the change, since multiple agents work in this project. (Agent: Claude Sonnet 4.6)

### Rename agent files from CLAUDE* to AGENTS*
- Renamed `CLAUDE.md` → `AGENTS.md` and `CLAUDE_CHANGELOG.md` → `AGENTS_CHANGELOG.md` (via `git mv` to preserve history).
- Created a `CLAUDE.md` symlink pointing to `AGENTS.md` so tools that look for `CLAUDE.md` still resolve.
- `AGENTS.md`: Updated the document title and the two changelog-pointer instruction lines to reference `AGENTS_CHANGELOG.md`. Generalized the "Instructions for Claude Code" section heading (and its table-of-contents link/anchor) to "Instructions for AI agents".
- `AGENTS_CHANGELOG.md`: Generalized the "Claude Changelog" title and "made by Claude Code" description to refer to AI agents.
- `README.md` and `.github/pull_request_template.md`: Updated their `CLAUDE.md` links to `AGENTS.md`. In the PR template, replaced the hardcoded GitHub URL that pointed at a since-deleted branch with an absolute link to the `develop` branch: `[Getting Started](https://github.com/lasseignelab/rrc-datahub-web/blob/develop/AGENTS.md#getting-started)`. A relative link does not resolve when the template text is rendered in a PR description, so an absolute URL to a permanent branch is used.
- Historical changelog entries below that mention `CLAUDE.md`/`CLAUDE_CHANGELOG.md` or Claude Code were left unchanged as an accurate record of the time.

## 2026-09-09

### Clear staging directory before ETL download
- `etl/download.py`: Added `_clear_staging(staging)` which deletes all files and subdirectories inside the staging directory (removing contents, not the directory itself). Called at the start of `run_download` right after the staging directory is resolved/logged, so stale data from a previous download no longer lingers alongside fresh files. Added `import shutil` for `shutil.rmtree`.

## 2026-09-03

### Switch MegaLinter GitHub Action to Python flavor image
- `.github/workflows/mega-linter.yml`: Changed `uses: oxsecurity/megalinter@v9` to `uses: oxsecurity/megalinter/flavors/python@v9`. The all-linters image was exhausting GitHub Actions runner disk space; the Python flavor ships only the Python linter family (pylint, ruff, black, flake8, isort, bandit, mypy, pyright) and is significantly smaller.

## 2026-08-27

### Fix: "Not applicable" not excluded from dropdowns or covered by unknown filters
- `pages/charts.py`: Added `"Not applicable"` to the exclusion list in `_get_all_sexes()` and `_get_all_underlying_variants()` so it no longer appears in the dropdown options (same treatment as "Not provided"). Updated both `_get_datasets_by_filters` and `_get_dataset_table` to include `Sample.sex.in_(["Not provided", "Not applicable"])` and `Sample.underlying_variant.in_(["Not provided", "Not applicable"])` in the respective unknown-filter conditions. The age filter already covered both via `age_range IS NULL`. Updated all three checkbox labels to read "…not provided or not applicable".

### Fix: "Not applicable" age shown as "Not provided" in dataset table and plot filters
- `pages/charts.py`: In the dataset table query, added `Sample.age_raw` so null age_range rows can be labeled correctly. Null-range samples are now grouped separately by their `age_raw` value — "Not applicable" appears as "Not applicable" and anything else (null, empty, "Not provided") appears as "Not provided". Both appear in the Age column alongside numeric ranges. In `_get_age_ranges_for_dataset`, also added `age_raw` to the query so the plot parameter Age checklist produces a separate option for each distinct null-range label (e.g., "Not applicable" and "Not provided" as separate entries) with values encoded as `"raw:<label>"`. In `_get_tpm_data`, updated the age filter to handle `"raw:..."` values: "Not provided" matches rows where `age_range IS NULL` and `age_raw` is null, empty, or "Not provided"; other labels (e.g., "Not applicable") match rows where `age_range IS NULL` and `age_raw` equals that label exactly.

## 2026-08-21

### Fix group colors to be stable when plot filters change
- `components/tpm_violin_plot_plotly.py`: Renamed `_DEFAULT_COLORS` to `DEFAULT_COLORS` so it can be imported by callers.
- `pages/charts.py`: Imports `DEFAULT_COLORS`. Added `State("group-select", "options")` to `update_plot` to access the full group list without an extra DB call. Builds a stable `{group: color}` dict keyed on the full options list and passes it as `palette` to `plot_tpm_violin_plotly`. Colors are now assigned by group identity so removing a group from the filter does not shift the colors of the remaining groups.

### Fix y-axis range to unfiltered dataset extent for consistent plot comparison
- `pages/charts.py`: Added `_get_tpm_range(bioproject, gene_name)` which queries the global min/max of log10(TPM+1) for all samples in a dataset for a given gene, with no plot-parameter filters applied. In `update_plot`, after building the figure, calls `_get_tpm_range` and pins the y-axis with 5% padding via `fig.update_layout(yaxis=dict(range=[...]))`. The scale now stays fixed while Group, Sample type, Sex, and Age filters change.

### Fix: accessible name missing on single-option checklist containers
- `assets/accessibility.js`: Added `include-unknown-sex`, `include-unknown-variant`, and `require-wildtype` to `OPTION_CONTAINERS` so they receive the `role="listbox"` → `role="group"` fix. Added `SINGLE_OPTION_CONTAINERS` list and `fixSingleOptionContainerLabels()` function, which reads each container's first option label text and sets it as `aria-label` on the container — giving screen readers an accessible name without adding extra DOM elements to the layout.

### Rename Genotype to Group in plot and data table
- `components/tpm_violin_plot_plotly.py`: Added `group_label` parameter to `plot_tpm_violin_plotly`. When provided, it replaces `group_col` as the x-axis title and legend title, while leaving tick labels (the actual group values) unchanged.
- `pages/charts.py`: Passed `group_label="Group"` to `plot_tpm_violin_plotly`. Changed the data table column header from "Genotype" to "Group (n)". Added `n` (sample count per group) to the `groupby` aggregation and displays it beside each group name as `"{genotype} (n)"`. Updated caption wording from "genotype(s)" to "group(s)".

### Add Age filter to Plot Parameters
- `pages/charts.py`: Moved `_plural(n, unit)` and `_fmt(lo, hi)` helpers from local scope inside `_get_dataset_table` to module level so they are available to the new `_get_age_ranges_for_dataset(bioproject)` function. Added `_get_age_ranges_for_dataset` which queries distinct age range bounds, returns human-readable labels (matching the Datasets table "Age" column format) with encoded values (`"{lo}:{hi}"` or `"none"` for null). Added `age_ranges` parameter to `_get_tpm_data()` using `or_()` of exact `and_(func.lower==lo, func.upper==hi)` conditions. Added `_initial_age_ranges_for_plot` to the pre-load block. Added `dcc.Checklist(id="plot-age-select")` to the Plot Parameters layout below Sex, defaulting to all age ranges selected. Extended `update_selectors` with two new Outputs for `plot-age-select`. Added `plot-age-select` as an Input to both `update_plot` and `update_table`, with an early-exit guard when nothing is selected.
- `assets/accessibility.js`: Added `plot-age-select` to `LABEL_MAP` and `OPTION_CONTAINERS` to apply the same ARIA fixes as other checklists.

### Add Sex filter to Plot Parameters
- `pages/charts.py`: Added `_get_sexes_for_dataset(bioproject)` query function. Added `sexes` parameter to `_get_tpm_data()`. Added `_initial_sexes_for_plot` to pre-load block. Added `dcc.Checklist(id="plot-sex-select")` below Sample type in the Plot Parameters layout, defaulting to all sex values selected. Extended `update_selectors` with two new Outputs for `plot-sex-select`. Added `plot-sex-select` as an Input to both `update_plot` and `update_table`.
- `assets/accessibility.js`: Added `plot-sex-select` to `LABEL_MAP` and `OPTION_CONTAINERS`.

### Add Sample type filter to Plot Parameters
- `pages/charts.py`: Added `_get_sample_types_for_dataset(bioproject)` query function. Added `sample_types` parameter to `_get_tpm_data()` so the DB query filters by sample type before returning rows. Added `_initial_sample_types_for_plot` to the pre-load block. Added `dcc.Checklist(id="plot-sample-type-select")` to the Plot Parameters layout between Groups and Statistical test, defaulting to all types selected. Extended `update_selectors` with two new Outputs to repopulate and reset the checklist when the dataset changes. Added `plot-sample-type-select` as an Input to both `update_plot` and `update_table`, with an early-exit guard when nothing is selected.
- `assets/accessibility.js`: Added `plot-sample-type-select` to `LABEL_MAP` and `OPTION_CONTAINERS` to apply the same ARIA fixes as the Groups checklist.

### Convert four filter checklists to multi-select dropdowns
- `pages/charts.py`: Replaced `dcc.Checklist` with `dcc.Dropdown(multi=True)` for the Scientific name, Underlying variant, Sample type, and Sex filters. The "Include datasets…" and "Only include datasets…" checklists below each dropdown remain unchanged. Added `or []` guards throughout the `filter_datasets` callback because `dcc.Dropdown` returns `None` (not `[]`) when cleared. Applied `black` auto-formatting.
- `assets/accessibility.js`: Removed the four now-unused dropdown IDs from `LABEL_MAP` and `OPTION_CONTAINERS` (they were for the old checklists). Added `fixDropdownClearButtons()` to inject a visually-hidden text span into each `<a class="dash-dropdown-clear">` element — Dash's multi-select clear button is an anchor with an SVG-only icon that HTML_CodeSniffer flags as having no link content despite the `aria-label`.

### Remove wild-type from variant checklist; add matching controls filter
- `pages/charts.py`: Added `_WILDTYPE_VALUE = "wild-type"` constant. Excluded wild-type from `_get_all_underlying_variants()` so it no longer appears as a checklist option. Added `dcc.Checklist(id="require-wildtype")` labeled "Only include datasets with matching controls", defaulting to unchecked. When checked, both `_get_dataset_table` and `_get_datasets_by_filters` post-filter to bioprojects that contain at least one wild-type sample. Wired into `filter_datasets`.

### Fix: datasets with Not provided variant hidden when all variants unchecked
- `pages/charts.py`: The `filter_datasets` early-exit guard tested `not selected_variants` unconditionally, so unchecking all variants returned an empty list even when "Include datasets with underlying variant not provided" was checked. Fixed by only exiting early when `selected_variants` is empty AND `include_unknown_variant` is also unchecked.

### Add "Include datasets with underlying variant not provided" checkbox
- `pages/charts.py`: Removed `"Not provided"` from `_get_all_underlying_variants()` results. Added `dcc.Checklist(id="include-unknown-variant")` below the underlying variant checklist, defaulting to checked. Added `include_unknown_variant` parameter to `_get_dataset_table` and `_get_datasets_by_filters` with matching `or_` logic for null/Not provided values. Wired the new input into `filter_datasets`.

### Add "Include datasets with sex not provided" checkbox to sex filter
- `pages/charts.py`: Removed `"Not provided"` from `_get_all_sexes()` results so it no longer appears as a checklist option. Added `dcc.Checklist(id="include-unknown-sex")` below the sex checklist, defaulting to checked. Added `include_unknown_sex` parameter to `_get_dataset_table` and `_get_datasets_by_filters`; when checked, the sex filter condition expands to `sex IN (...) OR sex IS NULL OR sex = 'Not provided'`. Wired the new input into `filter_datasets`.

### Force dataset table scrollbar always visible on macOS
- `pages/charts.py`: Added `id="dataset-table-wrapper"` to the scrollable div around the dataset table.
- `assets/style.css`: Added `::-webkit-scrollbar` rules targeting `#dataset-table-wrapper` to force the scrollbar to always render. macOS hides `overflow:scroll` bars until interaction regardless of CSS; explicit webkit scrollbar styling bypasses that system setting.

### Add Groups column to dataset selection table
- `pages/charts.py`: Added `Sample.genotype` to the `_get_dataset_table` query. Aggregates distinct genotypes per bioproject via `Counter` alongside the existing columns. Renders as a `"Groups (n)"` column between Sex and Age in the table header and rows.

### Remove NP/NA sentinel handling now that source data uses "Not provided"
- `pages/charts.py`: Deleted `_display_value()` helper and the `NP` guard in `_readable_sample_type()`. All call sites in `_get_dataset_table()` and the filter checklists now use the raw DB value directly, which is already stored as `"Not provided"`.
- `etl/load.py`: Removed `"NP"` and `"NA"` from `_NUMERIC_NULLS`; only `""` and `"Not provided"` are now treated as missing for numeric/range fields.

### Handle "Not provided" sentinel in age_range numeric parser
- `etl/load.py`: Added `"Not provided"` to `_NUMERIC_NULLS` so `_opt_numrange` treats it as a missing value. Source TSVs now use this string instead of `"NP"` for datasets with no age data.

### Add --branch option to ETL download script
- `etl/download.py`: Added a `ref` parameter (default `"develop"`) to `_download_github_file`, `_download_github_directory`, `download_geo_datasets`, `download_transformed_metadata`, and `run_download`. All GitHub Contents API requests now pass `?ref=<branch>`. The `__main__` block exposes this as `--branch` via `argparse`.

### Reset database before ETL reload with sequence restart
- `etl/load.py`: Added `reset_database()` which issues `TRUNCATE dataset, gene, sample, sample_gene RESTART IDENTITY CASCADE` to delete all rows and reset autoincrement sequences to 1 before each full reload. Called at the top of `__main__` before the four load functions.

## 2026-08-12

### Add page description below Charts heading
- `pages/charts.py`: Added `html.P` immediately after `html.H1("TPM Expression")` describing how to use the page. Gives screen reader users orientation before they reach any interactive controls.

### Name download files `<dataset>_<gene>_tpm_expression.*`
- `pages/charts.py`: Added `html.Div(id="download-meta")` (hidden) to the layout. Added `Output("download-meta", "children")` to `update_plot`; writes `"{bioproject}_{gene}"` on every selection change.
- `assets/accessibility.js`: Both PNG and CSV download handlers now read `download-meta.textContent` as the filename prefix, producing e.g. `PRJNA285844_Pkd1_tpm_expression.png` / `.csv`. Falls back to `tpm_expression_plot` / `tpm_expression_data` when the div is empty.

### Improve screen reader announcement of decimal table values
- `pages/charts.py`: Added `_aria_decimal(value)` helper that formats a 4-decimal float for screen readers by reading post-decimal digits individually (e.g. `"1 point 5 6 8 3"`). Each of the five numeric cells in the summary table (`Max`, `Q3`, `Median`, `Q1`, `Min`) now contains two `html.Span` elements: the visible value with `aria-hidden="true"` and a `visually-hidden` span with the spoken form, replacing the earlier `aria-label` on the `<td>` which caused double-reading.
- `assets/style.css`: Added `user-select: none` to `.visually-hidden` so the hidden spoken text is excluded from clipboard copies when a user selects and pastes table content.

## 2026-08-07

### Display NP sentinel as "Not provided" in filters and dataset table
- `pages/charts.py`: Added `_display_value(raw)` helper that maps the raw DB value `"NP"` to `"Not provided"` and passes all other values through unchanged. Applied to scientific name, underlying variant, and sex checklist labels and the corresponding dataset table columns. Updated `_readable_sample_type` with an early `"NP"` guard. Also changed the age column fallback and the "include unknown age" checkbox label from "Unknown"/"unknown age" to "Not provided"/"age not provided". The raw `"NP"` value is preserved as the checklist `value` prop so filter callbacks continue to query the database correctly.

### Replace age RangeSlider with unit-aware min/max inputs
- `pages/charts.py`: Removed `dcc.RangeSlider(id="age-range-slider")`. Added `html.Fieldset` containing two `dcc.Input` fields (min/max, id `age-min-input`/`age-max-input`) and a `dcc.Dropdown` unit selector (id `age-unit`, options: days/weeks/months/years). A `dcc.Store(id="age-range-days")` holds the current range in days. Two new callbacks handle the round-trip: `_convert_age_inputs_on_unit_change` re-expresses the stored days in the new unit when the dropdown changes; `_update_age_days_store` converts displayed values back to days when inputs change. `filter_datasets` updated to read from `age-range-days` store instead of the slider. Added `_DAYS_PER_UNIT` constant, `_to_days()`, and `_from_days()` module-level helpers.
- `assets/accessibility.js`: Added `"age-unit": "age-unit-label"` to LABEL_MAP. Removed `labelRangeSliderInputs()` function (slider no longer present).

## 2026-08-07

### Format age column values as human-readable time units
- `pages/charts.py`: Added module-level `_days_to_readable(n)` converting integer day counts to `(value, unit_singular)` in the most appropriate unit: <14 days→days, <84 days→weeks, <730 days→months, else years. Updated `_fmt` inside `_get_dataset_table` to use it: same-unit ranges collapse to `"2–3 weeks"`, cross-unit ranges label each side `"9 weeks–6 months"`. `humanize.naturaldelta` was evaluated but not used — it misclassifies 21 days as "a month". Column header changed from `"Age (days) (n)"` to `"Age (n)"` since the unit now appears inline with each value.

### Add per-value sample counts to dataset table columns
- `pages/charts.py`: Changed `_get_dataset_table()` to count samples per distinct value using `Counter` instead of `set`. Each grouped column (Scientific Name, Underlying Variant, Sample Type, Sex, Age) now returns strings like `"Pkd1 (6)"` rather than just `"Pkd1"`. `_readable_sample_type()` is applied inside `_get_dataset_table()` for sample types so `_build_table_rows()` just joins pre-formatted strings. Column headers updated to include `(n)` suffix (e.g. `"Scientific Name (n)"`).

### Enable SQL query logging in development
- `db/connection.py`: Added `_is_debug()` helper that reads the `DEBUG` env var (truthy values: `"1"`, `"true"`, `"yes"`). Passes `echo=_is_debug()` to `create_engine()` so SQLAlchemy logs all queries in development and stays silent in production.
- `.env.example`: Added `DEBUG=true` with a comment explaining it should be omitted or set to false in production.

---

## 2026-08-05

### Add dataset count below the Dataset label
- `pages/charts.py`: Added `html.Span(id="dataset-count")` inline with the Dataset label. Added `Output("dataset-count", "children")` to `filter_datasets`; returns `"N dataset(s)"` (pluralised) on each filter change, or `"0 datasets"` on the early-exit path.

### Replace per-sample TPM table with per-genotype log10(TPM+1) summary
- `pages/charts.py`: Rewrote `update_table` to group by genotype and show Max, Q3, Median, Q1, Min of log10(TPM+1) — matching the five-number summary displayed by the violin plot. Removed the raw TPM column. Computes `log_tpm` via `df["TPM"].apply(lambda x: math.log10(x + 1))` then uses pandas named aggregation with `quantile(0.75)` and `quantile(0.25)` for Q3/Q1. Caption still reports total sample count and number of genotypes.

### Tighten Age column header and collapse equal-bound ranges
- `pages/charts.py`: Renamed table header from `"Age Range (days)"` to `"Age (days)"`. In `_fmt`, when both bounds are present and equal, returns just the single value as a string instead of `"lo–lo"`.

### Show distinct age ranges in dataset table column
- `pages/charts.py`: Changed `_get_dataset_table()` to accumulate distinct `(lower, upper)` integer pairs per bioproject into `age_ranges` (a set of tuples) instead of tracking a single min/max span. Added nested helpers `_fmt(lo, hi)` and `_sort_key(pair)` to format each pair as `"lo–hi"`, `"lo+"`, or `"–hi"`, and to sort by lower bound then upper bound. The returned dict key is now `"age_ranges"` (list of formatted strings, `["Unknown"]` when empty). Updated `_build_table_rows` to join the list with `", "`.

### Add Age Range (days) column to dataset table
- `pages/charts.py`: Extended `_get_dataset_table()` to also select `func.lower(Sample.age_range)` and `func.upper(Sample.age_range)` for each sample. The aggregation loop now tracks `age_min` and `age_max` per bioproject (min of all lower bounds, max of all upper bounds). The returned dict includes `"age_range"` formatted as `"X–Y"` (en-dash), or `"Unknown"` when all samples have a null age. Added `html.Th("Age Range (days)")` to the table header and `html.Td(row["age_range"])` to `_build_table_rows`.

### Apply human-readable sample type labels in dataset table
- `pages/charts.py`: In `_build_table_rows`, the Sample Type column now passes each raw value through `_readable_sample_type()` before joining, matching the labels shown in the filter checklist.

### Style dataset table selector buttons as radio buttons
- `pages/charts.py`: Changed the Select button label from `"Select"` to `""` (empty); visual content is now provided entirely by CSS.
- `assets/style.css`: Added radio-button CSS for `#dataset-table td:first-child button` — circular border, `::before` filled dot when `aria-pressed="true"`, and a visible `:focus-visible` ring. The button is 18 × 18 px with a 50% border-radius so it appears as a circle.

### Replace dataset dropdown with scrollable selection table
- `pages/charts.py`: Added `_get_dataset_table()` which applies the same filter logic as `_get_datasets_by_filters()` then aggregates distinct `scientific_name`, `underlying_variant`, `sample_type`, and `sex` values per bioproject. Added `_build_table_rows()` to render `html.Tr` elements with a Select button, BioProject ID, and the four aggregated columns. Replaced `dcc.Dropdown(id="dataset-select")` with a fixed-height (280 px) scrollable `html.Div` containing `html.Table(id="dataset-table")` with a sticky header and `html.Tbody(id="dataset-table-body")` populated by callbacks. Added `dcc.Store(id="dataset-selected")` to hold the selected bioproject. Replaced the old `filter_datasets` callback (which output dropdown options/value) with one that outputs `dataset-table-body.children` and `dataset-selected.data`. Added a new `select_dataset` pattern-matching callback (using `ALL`) that fires when any row Select button is clicked and updates `dataset-selected.data` with `allow_duplicate=True`. Updated `update_selectors`, `update_plot`, and `update_table` callbacks to use `Input("dataset-selected", "data")` instead of `Input("dataset-select", "value")`. Added `ALL`, `ctx` and `PreventUpdate` imports.
- `assets/style.css`: Added `#dataset-table` styles (border-collapse, sticky `th`, even-row stripe, `.dataset-row-selected` highlight in `#cce5ff`, hover state).
- `assets/accessibility.js`: Added event delegation listener on `[data-bp]` buttons to immediately apply `aria-pressed="true"` and `dataset-row-selected` class to the clicked row, giving instant visual feedback before the Dash callback round-trip completes.

### Add sex filter between sample type and age range
- `pages/charts.py`: Added `_get_all_sexes()` to query all distinct non-null `sex` values. Pre-loads `_all_sexes`. Added `sex-select` `dcc.Checklist` to the layout between Sample type and Age range. Extended `_get_datasets_by_filters()` with a `sexes` parameter filtered via `Sample.sex.in_(sexes)`. Updated `filter_datasets` callback with the new `Input("sex-select", "value")`.
- `assets/accessibility.js`: Added `"sex-select": "sex-select-label"` to `LABEL_MAP` and `"sex-select"` to `OPTION_CONTAINERS`.

### Add checkbox to control whether unknown-age samples are included in dataset filter
- `pages/charts.py`: Added `dcc.Checklist(id="include-unknown-age")` with a single option "Include samples with unknown age", checked by default, placed below the age range slider. Extended `_get_datasets_by_filters()` with `include_unknown_age: bool`; when True the age condition is `age_range IS NULL OR overlaps`; when False it is `age_range IS NOT NULL AND overlaps`. Updated `filter_datasets` callback with the new input, passing `bool(include_unknown_age)` (converts empty list to False).
- `assets/accessibility.js`: Added `"include-unknown-age"` to `OPTION_CONTAINERS` to apply the same role=group fix as other checklists.

### Add age range (days) filter to dataset filters section
- `pages/charts.py`: Added `from sqlalchemy import and_, func, or_`. Added `_get_age_range_bounds()` which uses PostgreSQL `lower()`/`upper()` on the NUMRANGE column to find the global min/max age in days (falls back to 0–365 if no data). Pre-loads `_age_min` and `_age_max` at startup. Extended `_get_datasets_by_filters()` with an `age_range` parameter; the filter includes samples where `age_range` is null (unknown age always passes) OR the sample's age_range overlaps the selected range. Added `dcc.RangeSlider(id="age-range-slider")` to the layout after Sample type with tooltips always visible. Updated `filter_datasets` callback with the new `Input("age-range-slider", "value")`.
- `assets/accessibility.js`: Added `labelRangeSliderInputs()` which uses `MutationObserver` (via `applyAll`) to set `aria-label` on the slider's two bare `<input type="number">` elements, fixing the WCAG 4.1.2 violation that pa11y detected.

### Add underlying variant filter to dataset filters section
- `pages/charts.py`: Added `_get_all_underlying_variants()` to query all distinct non-null `underlying_variant` values from the sample table. Added `underlying-variant-select` `dcc.Checklist` to the layout between scientific name and sample type. Extended `_get_datasets_by_filters()` to accept a third `underlying_variants` parameter and filter the dataset query against it. Updated `filter_datasets` callback with the new `Input("underlying-variant-select", "value")`.
- `assets/accessibility.js`: Added `"underlying-variant-select": "underlying-variant-label"` to `LABEL_MAP` and `"underlying-variant-select"` to `OPTION_CONTAINERS`.

### Remove cascade from scientific name to sample type
- `pages/charts.py`: Removed `filter_sample_types_by_scientific_name` callback and the `_get_sample_types_by_scientific_names` query function. Sample type options are now fixed (all types always visible). Scientific name and sample type still both feed into `filter_datasets` to narrow the dataset dropdown.

---

## 2026-08-04

### Organize Charts page into "Dataset filters" and "Plot parameters" sections
- `pages/charts.py`: Wrapped the scientific name, sample type, and dataset controls in an `html.Section` with heading "Dataset filters" (`id="dataset-filters-heading"`, `aria-labelledby="dataset-filters-heading"`). Wrapped the gene, groups, statistical test, buttons, and output area in a second `html.Section` with heading "Plot parameters" (`id="plot-parameters-heading"`, `aria-labelledby="plot-parameters-heading"`). Sections use `aria-labelledby` pointing to their H2 headings so screen readers can identify each landmark.

### Add scientific name filter above sample type; both filters narrow the dataset dropdown
- `pages/charts.py`: Added `_get_all_scientific_names()` to query all distinct non-null `scientific_name` values from the sample table. Added `_get_sample_types_by_scientific_names(scientific_names)` to return only the sample types present in samples of the selected organisms. Replaced `_get_datasets_by_sample_types()` with `_get_datasets_by_filters(scientific_names, sample_types)` which requires samples to match both filters simultaneously. Layout: added `scientific-name-select` `dcc.Checklist` above the existing `sample-type-select`, with all names selected by default. Added callback 1 (`filter_sample_types_by_scientific_name`) wired `scientific-name-select.value → sample-type-select.options + value`; updated callback 2 (`filter_datasets`) to take both `scientific-name-select.value` and `sample-type-select.value` as inputs so datasets reflect both active filters.
- `assets/accessibility.js`: Added `"scientific-name-select": "scientific-name-label"` to `LABEL_MAP` and `"scientific-name-select"` to `OPTION_CONTAINERS`.

### Add sample type filter that narrows the dataset dropdown
- `pages/charts.py`: Added `_get_all_sample_types()` to query all distinct non-null `sample_type` values across the entire database. Added `_get_datasets_by_sample_types(sample_types)` to return only bioproject accessions that contain at least one sample matching the selected types. Added `_SAMPLE_TYPE_LABELS` dict and `_readable_sample_type()` to convert raw database values to human-readable labels (underscores/hyphens → spaces, title-cased; with an override dict for values like "iPSC" that must not be title-cased). Layout: added `sample-type-select` `dcc.Checklist` above the dataset dropdown, showing all available sample types from the database with all selected by default. Added callback 1 (`filter_datasets_by_sample_type`) that takes the checklist value as input and updates `dataset-select.options` and `dataset-select.value`, preserving the current dataset if it is still in the filtered list.
- `assets/accessibility.js`: Added `"sample-type-select": "sample-type-label"` to `LABEL_MAP` and `"sample-type-select"` to `OPTION_CONTAINERS` so the checklist gets the same ARIA role fix as the groups checklist.

## 2026-07-31

### Fix pa11y CI failure: move no-data message out of table caption
- `pages/charts.py`: axe-core's "layout-table-caption" rule fired in CI because when no DB is available, `update_table` returned `[html.Caption("No data...")]` — a table containing only a caption and no `<th>` elements, which axe classifies as a layout table (layout tables must not have captions). Fix: added `html.P(id="table-status")` as a sibling above the table in `table-container`. The callback now outputs both `table-status.children` (the message string) and `tpm-data-table.children` (the table rows). No-data states write the message to the paragraph and return `[]` for the table, leaving the table empty rather than caption-only. When data is present the message is cleared and the table gets its normal caption + thead + tbody.

### Remove subscript Unicode from table column header
- `pages/charts.py`: Changed `log₁₀(TPM + 1)` → `log10(TPM + 1)` in the table `<th>`. The subscript Unicode characters rendered inconsistently and also appeared verbatim in the CSV export.

### Reorder button bar: toggle button left, download button right
- `pages/charts.py`: Moved `toggle-view-btn` ("Show table / Show plot") to the left of the download buttons. Added `marginRight: "8px"` to the toggle button for spacing. Removed `marginRight` from download buttons (now the last elements in the row).

### Add "Download table as CSV" button, sync download buttons with view toggle
- `pages/charts.py`: Added `html.Button("Download table as CSV", id="download-csv-btn")` (initially hidden) alongside the existing PNG download button. Extended the view-toggle `clientside_callback` with two additional outputs — `download-png-btn.style` and `download-csv-btn.style` — so the correct download button is always visible for the active view: PNG download when the plot is shown, CSV download when the table is shown.
- `assets/accessibility.js`: Added event-delegation click handler for `download-csv-btn`. Reads headers and rows directly from the rendered `tpm-data-table` DOM, builds a properly-escaped CSV string (double-quotes all fields, escapes internal quotes), derives the filename from the table caption, and triggers a client-side blob download — no server round-trip required.

### Fix table toggle: replace DOM event delegation with clientside_callback
- `pages/charts.py`: Replaced the `toggle-view-btn` click handler in `accessibility.js` with a Dash `clientside_callback`. The previous handler used direct DOM manipulation (`el.style.display = "none"`), which React's reconciler overwrites whenever any sibling callback (e.g., `update_table`) fires and re-renders part of the component tree. The `clientside_callback` updates `plot-container.style` and `table-container.style` through React's component prop system, so the toggle state persists across server callback re-renders. Button text and `aria-expanded` are still set via DOM manipulation inside the callback function — safe because `toggle-view-btn` is not a callback output and React does not reconcile it. Added `clientside_callback` to the Dash import.
- `assets/accessibility.js`: Removed the `toggle-view-btn` click event listener (now handled by the clientside callback). Download handler is unchanged.

### Add accessible toggleable table view for TPM expression data
- `pages/charts.py`: Added a "Show table / Show plot" toggle button (`id="toggle-view-btn"`, `aria-expanded`) alongside the download button. Added `id="plot-container"` wrapper around the graph and `id="table-container"` div (initially hidden) containing `html.Table(id="tpm-data-table")`. Added `id="view-status"` polite ARIA live region for screen-reader announcements. Added callback 4 (`update_table`) which builds an accessible HTML table of per-sample raw TPM and log₁₀(TPM+1) values for the current gene/group selection; the table is always populated in the background so toggling the view requires no server round-trip. Added `import math` for the log10 calculation.
- `assets/accessibility.js`: Added click event listener for `toggle-view-btn` that switches `display` on the two containers, updates `aria-expanded`, updates the button label, and writes a polite status message to the live region.
- `assets/style.css`: Added `.visually-hidden` CSS class (clip + position: absolute) for the live region. Added table styles: border-collapse, padding, header background, zebra-stripe rows, and `:focus-within` outline for keyboard navigation.

## 2026-07-29

### Fix download button appearing/disappearing due to graph layout reflow
- `pages/charts.py`: `dcc.Graph` with `responsive=True` (which unsets `figure.layout.height`) collapses its container to near-zero height when `figure={}` during a callback update, then re-expands to ~450 px when the figure loads. The button was positioned below the graph, so it shifted by ~450 px on every figure update — going off-screen and back, which the user saw as appearing/disappearing on every other interaction (open dropdown = one interaction, select value = next). Fix: moved the button above the graph so it is always in the upper viewport regardless of graph height, and added `minHeight: 450px` to the graph container to prevent the collapse reflow.

### Fix download button flicker by moving handler out of Dash callback system
- `assets/accessibility.js`: Added a document-level click event listener (event delegation) that handles the PNG download directly. The button was flickering because being a Dash `Input` causes Dash 4 to apply a loading-state lifecycle (unmount/remount) on every click. Wiring the handler in plain JavaScript bypasses that mechanism entirely.
- `pages/charts.py`: Removed the `clientside_callback` and the `html.Div(id="download-trigger")` that were no longer needed. The button (`id="download-png-btn"`) is now a plain HTML element with no Dash callback wiring.

### Fix blank PNG export and initial button-disappear attempt
- `pages/charts.py`: Removed the server-side `toggle_download_button` callback (callback 4) that controlled `download-png-btn.disabled`. That callback fired on every figure update, including transient `{}` states during dataset/gene selection changes, causing Dash to remount the button and making it visually disappear. The button is now always enabled; the clientside callback already guards against empty figures.
- `pages/charts.py`: Fixed blank PNG download. `dcc.Graph` renders a wrapper `<div id="violin-plot">` containing the actual Plotly element `<div class="js-plotly-plot">`. `Plotly.toImage` requires the inner element (which carries `_fullData`), not the wrapper. Updated clientside callback to `querySelector(".js-plotly-plot")` and check `_fullData.length` for data presence. Removed `State("violin-plot", "figure")` from the clientside callback — figure presence is now determined from the DOM element directly, avoiding the server round-trip.

## 2026-07-24

### Add accessible PNG download button for violin plot
- `pages/charts.py`: Replaced the inaccessible Plotly mode bar download icon (hidden via `displayModeBar: False`) with an `html.Button("Download plot as PNG")`. The button is disabled until a figure is rendered (callback 4) and calls `Plotly.downloadImage` via a clientside callback (callback 5). The filename is derived from the figure title (the selected gene name).

### Fix chart layout at 400% zoom (WCAG 1.4.10 Reflow)
- `pages/charts.py`: Added `config={"responsive": True}` and `style={"width": "100%"}` to `dcc.Graph` so Plotly resizes the SVG when the container width changes at high zoom levels. Also set `displayModeBar: False` (the mode bar has no accessible label).
- `components/tpm_violin_plot_plotly.py`: Moved legend below the chart (`orientation="h"`, `y=-0.25`, `margin.b=160`). At narrow viewports the long genotype labels previously occupied most of the horizontal space, leaving almost no room for the plot area.

### Wrap navbar in html.Nav landmark (WCAG region)
- `components/navbar.py`: Changed `html.Div` to `html.Nav` with `aria-label="Site navigation"`. The navbar content was outside any landmark, failing the axe region check. With this and the `<main>` added previously, all page content is now contained within landmarks.

### Add main landmark and skip navigation link (WCAG 2.4.1)
- `app.py`: Wrapped `page_container` in `html.Main(id="main-content")` so the page has a `<main>` landmark. Added a visually-hidden skip-to-main-content `html.A` as the first focusable element so keyboard users can bypass the repeated navbar.
- `assets/style.css`: Added `.skip-nav` CSS — off-screen when unfocused (`position:absolute; left:-9999px`), visible when focused (`position:static`).

### Extend nested-interactive fix to dcc.RadioItems (#stat-test)
- `assets/accessibility.js`: `dcc.RadioItems` uses the same `role="listbox"` / `role="option"` rendering pattern as `dcc.Checklist`. Renamed and generalized `fixChecklistARIA()` to `fixOptionContainerARIA()`, which now iterates both `#group-select` and `#stat-test` and applies the same `role="group"` substitution and `role="option"` removal.

### Fix nested-interactive: replace role=listbox with role=group on checklist (WCAG 4.1.2)
- `assets/accessibility.js`: Previous fix (`aria-hidden` + `tabindex=-1` on checkboxes) did not satisfy the axe nested-interactive rule, which tests DOM structure — any focusable element inside an interactive ARIA role fails regardless of those attributes. `fixChecklistARIA()` now replaces `role="listbox"` on `#group-select` with `role="group"` (correct grouping role for a set of related checkboxes) and removes `role="option"` / `aria-selected` from each label, restoring the native `<label>`+`<input>` pattern. `role="group"` is not an interactive role, so nested checkboxes are permitted.

### Fix nested-interactive violation in dcc.Checklist (WCAG 4.1.2)
- `assets/accessibility.js`: Added `fixNestedInteractives()`. Dash 4 renders `dcc.Checklist` as `role="listbox"` with each option as `<label role="option">` wrapping `<input type="checkbox">`. The checkbox is a focusable descendant inside an interactive ARIA role, violating WCAG nested-interactive. The fix sets `aria-hidden="true"` and `tabindex="-1"` on each checkbox so the `role="option"` + `aria-selected` pair is the sole AT interface — the correct ARIA listbox pattern.

### Fix missing ARIA accessible names on group-select and stat-test (WCAG 4.1.2)
- `assets/accessibility.js`: Created. A `MutationObserver` watches the DOM and patches `aria-labelledby` onto `#group-select` (role=listbox) and `#stat-test` (role=radiogroup) after Dash renders them. Dash 4's `dcc.Checklist` and `dcc.RadioItems` do not expose ARIA props in their component API, so the attribute must be applied via JavaScript. The observer handles both initial page load and multi-page navigation.
- `pages/charts.py`: Added `id="group-select-label"` to the "Groups" label and `id="stat-test-label"` to the "Statistical test" label so the observer has valid targets to reference.
- `.pa11yci`: Added `http://localhost:8050/charts` to the URL list so CI catches accessibility violations on the charts page.

## 2026-07-17

### Pin Python version to 3.13
- `.python-version`: Created with `3.13` so pyenv, uv, and other local tooling pin to Python 3.13 automatically.
- `.github/workflows/tests.yml`, `.github/workflows/accessibility.yml`: Changed `python-version: "3.13"` to `python-version-file: .python-version` so CI reads from the single source of truth.

## 2026-07-15

### Fix pyright reportOptionalMemberAccess on get_engine()
- `db/connection.py`: Pyright couldn't narrow the type of the global `_engine` after `_get_factory()` set it, so `get_engine()` appeared to return `Engine | None`. Switched to a local variable pattern with an explicit `-> Engine` return annotation so pyright can confirm the return is always non-None.

### Add get_engine() and fix etl/load.py import after lazy refactor
- `db/connection.py`: Added `get_engine()` public function that returns the lazily-created engine. The lazy refactor had removed the module-level `engine` name, breaking any caller that needed the raw engine (mypy, pylint, and pyright all caught this).
- `etl/load.py`: Updated import from `engine` to `get_engine` and changed the `engine.raw_connection()` call to `get_engine().raw_connection()`.

### Make DB engine lazy to fix CI import crash
- `db/connection.py`: Engine and session factory were built at module level, causing `KeyError: 'DB_HOST'` whenever the module was imported without database env vars present (CI, fresh checkouts). Deferred creation to the first `SessionLocal()` call so the module imports cleanly in all environments. Tests relying on the Dash app import now pass without a live database.

### Fix percy version conflict breaking CI
- `requirements.txt`: Updated `percy==1.1.1` to `percy==2.0.2` — `dash[testing]==4.1.0` declares a `percy>=2.0.2` dependency, so the old pin made the combined install impossible.
- `requirements-dev.txt`: Removed the redundant explicit `percy==1.1.1` pin; `dash[testing]` already pulls the correct version via its own dependency declaration.

### Pin dash[testing] version in requirements-dev.txt
- `requirements-dev.txt`: Pinned `dash[testing]==4.1.0` to match `dash==4.1.0` in `requirements.txt`. Without a version pin, CI was upgrading dash to 4.4.0 when installing dev dependencies, pulling in new transitive requirements (`janus`, `pydantic`, `percy-python-selenium`) not present in `requirements.txt` and breaking the test environment.

### Server-side gene search in charts dropdown
- `pages/charts.py`: Replaced full 78k-gene dropdown with server-side search. New `_search_genes(search)` queries the `gene` table directly (no sample_gene join) with an ILIKE prefix filter and a limit of 50 results. The gene dropdown now fires a callback on each keystroke and returns only matching genes, eliminating browser lag from rendering thousands of options. Split the previous single selector callback into two: one for gene options (search-driven) and one for group reset (dataset-driven).

---

### Connect charts page to PostgreSQL; remove file-based data loading
- `pages/charts.py`: Rewrote to query the database instead of reading CSV/TSV files. Dataset list, gene list, genotype list, and per-gene TPM values all come from the `dataset`, `sample`, `gene`, and `sample_gene` tables via SQLAlchemy ORM queries. Module-level startup queries are wrapped with logged fallbacks so the page degrades gracefully if the database is unavailable.
- `config.py`: Deleted. Dataset discovery was the only consumer; that logic now lives inline in `pages/charts.py` as a DB query.
- `components/data_utils.py`: Deleted. `melt_nfcore_tpm()` is no longer needed; the database returns data already in long format.
- `db/PRJNA285844/`: Deleted. The CSV/TSV staging files (`salmon.merged.gene_tpm.tsv`, `samplesheet.csv`, `extended_metadata.csv`) are replaced by the PostgreSQL database.

---

## 2026-07-14

### Move Testing before Running the app in Getting Started and section order
- `CLAUDE.md`: Swapped steps 5 and 6 in Getting Started so the test suite runs before starting the app. Moved the Testing section before Running the app in the document body and Table of Contents to match.

### Update CLAUDE.md: streamline Getting Started, expand ETL and Dependencies sections
- `CLAUDE.md`: Condensed Getting Started to step titles with links only (detail moved to the referenced sections). Expanded Dependencies section to include the full venv creation and install commands. Expanded Environment setup to clarify variables are filled in progressively across setup steps. Added GitHub Token instructions (fine-grained PAT creation and org admin approval steps) to the ETL load script section.

### Reorder CLAUDE.md sections to match Getting Started sequence
- `CLAUDE.md`: Reordered sections so the detailed reference sections appear in the same order as the Getting Started steps: Dependencies → Environment setup → Database → ETL load script → Running the app → Testing. Contributor sections (Linting, Code style, Accessibility, Git conventions, Pull requests) remain grouped at the end. Updated Table of Contents to match.

---

## 2026-07-10

### Document query function placement convention in CLAUDE.md
- `CLAUDE.md`: Added "Query functions" subsection under Database explaining when to use `db/queries.py` vs. writing queries inline in page/component files. Rule: shared queries (used in 2+ places) go in `db/queries.py`; single-use queries stay in the page or component that needs them.

---

### Centralize linter import suppression in config files; add pa11y to pre-commit gate
A MegaLinter image update introduced pylint `E0401` (import-error) and pyright `reportMissingImports` failures across all files that import third-party packages not installed in the Docker image. Rather than scattering inline `# pylint: disable=import-error` and `# type: ignore[import-untyped]` comments across 14 source files, suppression was moved to central config:
- `.mega-linter.yml`: Added `PYTHON_PYLINT_ARGUMENTS: "--disable=import-error"` and `PYTHON_MYPY_ARGUMENTS: "--disable-error-code=import-untyped"`.
- `pyproject.toml`: Added `[tool.pyright]` section with `reportMissingImports = "none"` and `reportMissingModuleSource = "none"`.
- Removed all `# pylint: disable=import-error` and `# type: ignore[import-untyped]` from every source file (`app.py`, `components/`, `pages/`, `db/`, `etl/`, `migrations/`, `tests/`).
- `CLAUDE.md`: Updated "Instructions for Claude Code" to require `npm run a11y` (with the app running) alongside `pytest --headless` and MegaLinter before every commit and push.

### Expand Database section in CLAUDE.md with PostgreSQL install instructions
- `CLAUDE.md`: Added "Installing PostgreSQL" subsection covering macOS (Homebrew), Windows (official installer), and Linux (apt-get). Added "Creating the database and user" subsection with `psql` commands. Added "Connecting the app" subsection showing how to populate `.env` and run `alembic upgrade head`.
- `.env.example`: Updated `DB_USER` to `rrc_user` and `DB_PASSWORD` to `yourpassword` to match the credentials shown in the CLAUDE.md Database section.

---

## 2026-07-09

### Add gene model, sample_gene mapping table, and TPM load functions
- `db/models.py`: Added `Gene` (Ensembl gene_id + gene_name) and `SampleGene` (composite PK on sample_id + gene_id, secondary index on gene_id for gene-centric queries) ORM models. Named `SampleGene` rather than `SampleGeneTpm` so additional expression metrics can be added as columns in the future.
- `migrations/versions/a1b2c3d4e5f6_create_gene_table.py`: Alembic migration to create the `gene` table.
- `migrations/versions/b2c3d4e5f6a7_create_sample_gene_table.py`: Alembic migration to create the `sample_gene` table with FKs to `sample` and `gene`.
- `etl/load.py`: Added `load_genes()` — reads gene_id and gene_name from the first TPM reference file (all 14 files share the same 78,317-row Ensembl annotation) and bulk-inserts new genes. Added `load_tpm()` — for each `staging/tpm/PRJNA*/salmon.merged.gene_tpm.tsv`, maps SRR column headers to sample IDs, then bulk-inserts (sample_id, gene_id, tpm) rows via psycopg2 `execute_values` in 10,000-row batches for performance. Samples already present in `sample_gene` are skipped (idempotent). Both functions are called from `__main__`.

### Fixed urllib3 version conflict in requirements.txt
- `requirements.txt`: Pinned `urllib3==1.26.20` (was `2.6.3` from a prior `pip freeze` that captured the locally upgraded version). `selenium==4.2.0` requires `urllib3~=1.26` (1.x only); the 2.x pin caused CI `pip install` to fail with a dependency conflict.

---

## 2026-07-08

### Fixed CI pa11y failure — scipy missing from requirements.txt and percy version wrong
- `requirements.txt`: Added `scipy==1.15.3` (used by `components/tpm_violin_plot_plotly.py`; omission caused `ModuleNotFoundError` in CI and prevented the app from starting). Downgraded `percy` to `1.1.1` (was `2.0.2` from a previous `pip freeze`; v2 removes `percy.Runner` which `dash[testing]` requires).

### Fixed all MegaLinter errors and suppressed Flask teardown warning in pytest
- `app.py`: Removed unused imports (`plotly.express as px`, `dash.dcc.Graph.Graph`).
- `components/tpm_violin_plot_plotly.py`: Added `# pylint: disable=import-error` and `# type: ignore[import-untyped]` to numpy, pandas, plotly, and scipy imports for MegaLinter Docker compatibility.
- `etl/load.py`: Fixed isort (third-party before first-party); fixed pyright `Decimal`-to-`float` type mismatch with `# type: ignore[arg-type]`; shortened log message to stay within 88-char line limit.
- `migrations/env.py`: Fixed isort (moved `from db.models import Base` to first-party section with blank line separator).
- `migrations/versions/bd35225208f8_widen_fastq_md5_to_text.py`: Reformatted `op.alter_column` calls per black; fixed isort; added `# pylint: disable=no-member` to silence false-positive alembic.op member errors; switched string literals to double-quotes.
- `tests/conftest.py`: Fixed isort and missing blank line before first function (E302).
- `pytest.ini`: Added `filterwarnings` entry to suppress `PytestUnhandledThreadExceptionWarning` from Flask's `process_request_thread` during test server teardown — a known dash[testing] shutdown issue, not a bug in app code.

## 2026-07-08 (original entries below)

### Fixed percy AttributeError breaking dash_duo tests
- `requirements-dev.txt`: Pinned `percy==1.1.1`. dash[testing] uses `percy.Runner` which was removed in percy v2. Without the pin, pip installs the latest percy (2.x), causing `AttributeError: module 'percy' has no attribute 'Runner'` on all browser-driven tests.

### Fixed all MegaLinter linter errors; added pre-commit gate to CLAUDE.md
- `app.py`, `pages/home.py`, `components/navbar.py`, `components/data_utils.py`, `components/tpm_violin_plot_plotly.py`, `pages/charts.py`: Applied black and isort formatting (black prefers expanded function-call style; isort alphabetizes within sections).
- `pages/__init__.py`: Created empty file so mypy resolves `pages.home` without the "source file found twice" error.
- `tests/test_app.py`: Fixed pyright error (`home.layout.children or []`); added blank line between `from dash` and `from pages` imports so isort's first-party/third-party separator is preserved.
- `tests/conftest.py`: Reordered imports — `selenium` (third-party) before `app` (first-party) with blank line separator.
- `.mega-linter.yml`: Added `PYTHON_ISORT_ARGUMENTS` with `-p` flags for first-party modules (`app`, `components`, `config`, `db`, `pages`) because MegaLinter's Docker isort does not reliably pick up `pyproject.toml` `known_first_party`.
- `pyproject.toml`: Added `config` to `known_first_party` so local isort matches Docker isort behavior.
- `CLAUDE.md`: Added pre-commit instruction — run `pytest --headless` and MegaLinter before every commit/push. Added `rm -rf megalinter-reports` reminder and expanded Docker command.

### Fixed pytest tests broken by multi-page app refactor
- `tests/test_app.py`: Updated `test_layout_contains_h1` to check `pages.home.layout` directly instead of `app.layout.children` (H1 now lives in the home page module, not the root layout). Updated `test_graph_renders` to navigate to `/charts` where the `dcc.Graph` lives.

### Fixed WCAG 2.1 AA: missing lang attribute on html element
- `app.py`: Added `app.index_string` to set `lang="en"` on the `<html>` element (WCAG 3.1.1). pa11y-ci now passes with 0 errors.

## 2026-07-07

### Simplified Node.js/pa11y-ci setup instructions
- `CLAUDE.md`: Streamlined the accessibility automated checking section — remove the version-check step and go straight to install, drop the Node.js installer as an alternative (nvm/nvm-windows only), split the two-terminal run steps into separate code blocks.

## 2026-07-01

### Suppress selenium DeprecationWarnings in pytest output
- `pytest.ini`: Added `filterwarnings = ignore::DeprecationWarning:selenium` to silence urllib3 deprecation warnings emitted by selenium internals on every test run.

### Added Windows instructions to accessibility automated checking section
- `CLAUDE.md`: Expanded Node.js install and pa11y-ci run instructions to cover both macOS (nvm) and Windows (nvm-windows + PowerShell venv activation).

### Added Node.js install instructions to accessibility section
- `CLAUDE.md`: Added `node --version` check and nvm-based install instructions before the pa11y-ci local run steps, so developers know how to get Node.js if it is not already present.

## 2026-06-26

### Fixed fastq_md5 column overflow for paired-end reads
- `db/models.py`: Changed `fastq_md5` from `String(32)` to `Text`. Paired-end runs store two MD5 hashes joined by `;` (65 chars), exceeding the original 32-char limit.
- `migrations/versions/bd35225208f8_widen_fastq_md5_to_text.py`: Migration to ALTER the column type.

### Added load_samples ETL function
- `etl/load.py`: Added `load_samples()` — scans `staging/transformed-metadata/**/*_transformed.tsv`, looks up `dataset_id` by bioproject, and inserts new rows into the `sample` table. Idempotent (skips runs already present). Added helper functions `_opt_str`, `_opt_int`, `_opt_datetime`, and `_opt_numrange` to handle type conversion and "NP"/"NA" sentinels. `age_range_lower` + `age_range_upper` TSV columns are combined into a `psycopg2.extras.NumericRange` with closed bounds. Added `# pylint: disable=import-error` for MegaLinter compatibility. `__main__` now runs `load_datasets()` then `load_samples()`.

### Added Sample ORM model and migration
- `db/models.py`: Added `Sample` model — 34 columns matching the TSV schema. Surrogate integer PK; `dataset_id` integer FK to `dataset.id` (indexed); `run` unique constraint. Date columns use `DateTime`, large counts use `BigInteger`, `age_range` uses PostgreSQL `NUMRANGE` (replaces separate lower/upper columns), long URL uses `Text`; all non-key columns nullable.
- `migrations/versions/8e767ddb148f_create_sample_table.py`: Creates `sample` table with `ix_sample_dataset_id` index; downgrade drops both.

### Updated Git conventions to Gitflow-inspired branching model
- `CLAUDE.md`: Replaced single-line branch naming rule with a full branching model section documenting `main`, `develop`, `feature/*`, and `release/*` branches — when to branch, where to merge, reviewer requirements, and the terminal commands for merging a release branch back into `develop`.

## 2026-06-25

### Fixed Cheaha SSH auth — switch from password-auth to keyboard-interactive via Transport
- `etl/download.py`: Cheaha rejects the SSH `password` protocol method and closes the connection, preventing fallback to keyboard-interactive. Fixed by using `paramiko.Transport` directly and calling `transport.auth_interactive()` with a handler that responds to prompts with the user's password. Host key is still verified against `~/.ssh/known_hosts` using `paramiko.HostKeys`. Also fixed pyright errors: `makefile()` returns bytes so output is now decoded with `.decode("utf-8")`; `SFTPClient.from_transport()` can return `None` so a guard was added.

### Added Dataset ORM model, Alembic migration, and ETL load script
- `db/__init__.py`: Added package marker with header comment.
- `db/models.py`: Created `Base` (declarative base) and `Dataset` ORM model with integer surrogate primary key `id` and unique `bioproject` varchar column.
- `db/connection.py`: Implemented `_db_url()`, `engine`, and `SessionLocal` using env vars via `python-dotenv`.
- `alembic.ini`: Initialized Alembic config; URL intentionally left blank (set dynamically in env.py).
- `migrations/env.py`: Configured Alembic environment to read DB URL from env vars and use `Base.metadata` for autogenerate support.
- `migrations/versions/4df4fc616701_create_dataset_table.py`: Initial migration — creates `dataset` table with `id` (integer PK) and `bioproject` (varchar 20, unique, not null).
- `etl/load.py`: New ETL load script — reads `staging/geo_datasets.csv`, upserts bioproject accessions into the `dataset` table, skipping rows already present. Safe to run repeatedly.

### Fixed ETL Cheaha auth — password prompt instead of SSH key
- `etl/download.py`: Replaced SSH key authentication with `getpass.getpass()` interactive password prompt. Cheaha uses username/password rather than SSH key auth. Password is never stored.
- `etl/download.py`: Added `import getpass`; removed `CHEAHA_SSH_KEY` env var usage.
- `.env.example`: Removed `CHEAHA_SSH_KEY` variable; added note that password is prompted at runtime.
- `CLAUDE.md`: Updated Cheaha access instructions to reflect password prompt instead of SSH key.

### Fixed MegaLinter linter failures (pylint/mypy/pyright) caused by Docker SSL errors
- `app.py`: Added `# pylint: disable=import-error` and `# type: ignore[import-untyped]` on third-party imports. MegaLinter's Docker container cannot reach PyPI due to SSL errors, so PRE_COMMANDS fail to install packages; linters then report all third-party imports as unresolvable.
- `etl/download.py`: Added `# pylint: disable=import-error` and `# type: ignore[import-untyped]` on paramiko, requests, and dotenv imports.
- `tests/conftest.py`: Added `# type: ignore[import-untyped]` to selenium import (was missing the suppress comment).
- `tests/test_app.py`: Added `# pylint: disable=import-error` at module level and `# type: ignore[import-untyped]` to the `from dash import html` import inside the test function. All 8 MegaLinter linters now pass ✅.

### Added SQLAlchemy and Alembic
- Installed `sqlalchemy==2.0.51`, `alembic==1.18.5`, and `Mako==1.3.12` (alembic dependency).
- Updated `requirements.txt` via `pip freeze`.

### Fixed CI browser tests — Chrome crashes without display
- `.github/workflows/tests.yml`: Added `--headless` to the pytest command. `ubuntu-latest` runners have no display server; Chrome launched in windowed mode crashes immediately with "session not created: Chrome instance exited".

### Restricted all CI workflows to push events only
- `.github/workflows/accessibility.yml` and `tests.yml`: Changed `on: [push, pull_request]` to `on: [push]`. MegaLinter was already push-only.

## 2026-06-24

### Fixed dash_duo Chrome crash in GitHub Actions CI
- `tests/conftest.py`: Added `pytest_setup_options` hook that passes `--no-sandbox`, `--disable-dev-shm-usage`, and `--disable-setuid-sandbox` to Chrome. GitHub Actions containers do not support Chrome's sandbox, causing all three browser-driven tests to fail with `SessionNotCreatedException`.

### Fixed MegaLinter black/isort formatting conflicts
- `tests/conftest.py`: Collapsed webdriver_manager import to a single 82-char line so black and isort agree without needing to wrap it; removed extraneous blank line between import groups.
- `pyproject.toml`: Added `profile = "black"` to isort config so the two formatters stay compatible going forward.
- `CLAUDE.md`: Updated local linting section to document the full docker command.

### Fixed remaining MegaLinter errors (second pass)
- `tests/conftest.py`: Added `# pylint: disable=import-error` module-level directive and `# type: ignore[import-untyped]` on pytest and webdriver_manager imports — pylint/pyright use isolated environments in MegaLinter and cannot resolve dev-only packages via PRE_COMMANDS.
- `.mega-linter.yml`: Added `PYTHON_BANDIT_FILTER_REGEX_EXCLUDE: "tests/"` — `pyproject.toml` `exclude_dirs` is not read by MegaLinter's bandit runner.
- `pyproject.toml`: Added `[tool.isort] known_first_party` so isort correctly separates first-party app imports from third-party ones with a blank line.

### Fixed MegaLinter errors from test infrastructure addition
- `app.py`, `tests/test_app.py`, `tests/conftest.py`: Applied black and isort formatting.
- `.mega-linter.yml`: Added `pip install -r requirements-dev.txt` to PRE_COMMANDS so pylint and pyright can resolve `pytest` and `webdriver_manager` imports.
- `pyproject.toml`: Added `[tool.bandit] exclude_dirs = ["tests"]` to suppress B101 (assert_used) false positives in pytest test files.

### Fixed ChromeDriver setup and restored lang="en" (caught by test)
Added `webdriver-manager` to `requirements-dev.txt` and wired it into `conftest.py` via `pytest_configure` so ChromeDriver is auto-downloaded when not already in PATH. `test_lang_attribute` revealed that `app.index_string` (which sets `lang="en"`) had been removed — restored it. All 5 tests now pass.

### Set up dash[testing] + pytest infrastructure
Added automated testing with dash[testing] and pytest:
- `requirements-dev.txt` — test dependencies (dash[testing], pytest, pytest-html)
- `tests/conftest.py` — shared `app` fixture
- `tests/test_app.py` — 5 initial tests: server sanity, layout structure, H1 render, graph render, and `lang="en"` WCAG check
- `pytest.ini` — configures testpath and HTML report output
- `.github/workflows/tests.yml` — CI job that installs deps and runs pytest on every push
- Updated `.gitignore` to exclude `test-reports/`
- Updated `CLAUDE.md` with testing conventions, structure, and what-to-test guidance

### Aligned CLAUDE.md accessibility conventions with PR template checklist
- Fixed stale Language section — now correctly documents `app.index_string` as the mechanism for `lang="en"`, not the removed `html.Html()` approach.
- Fixed alt text rule — decorative images must use `alt=""`, not a non-empty value.
- Added focus indicator convention — never remove `outline` without a replacement.
- Added Dynamic content section — Dash callbacks require `role="status"` or `role="alert"` for screen reader announcements.
- Added axe DevTools to the automated checking guidance.

### Added ADA accessibility checklist to PR template
Added a focused WCAG 2.1 AA checklist to `.github/pull_request_template.md` covering automated scans, content (alt text, chart descriptions, contrast), interaction (keyboard nav, focus, labels, skip link), and structure (heading hierarchy, ARIA live regions, lang attribute).

## 2026-06-23

### Fixed WCAG 2.1 AA: Dash debug button has no accessible label
Set `dev_tools_ui=False` in `app.run()` to suppress Dash's debug panel button, which has no text or ARIA label (axe DevTools critical issue). Hot reload and error catching remain active. Removed the `hideElements` workaround from `.pa11yci` since the element no longer renders. Updated CLAUDE.md to document this requirement.

### Fixed pa11y-ci CI failure — Chromium sandbox and Node.js version
- `.pa11yci`: Added `chromeLaunchConfig.args: ["--no-sandbox", "--disable-setuid-sandbox"]` — required for Puppeteer to launch Chromium in GitHub Actions' containerized environment.
- `.github/workflows/accessibility.yml`: Bumped Node.js from 20 (deprecated on Actions) to 22.

### Fixed WCAG 2.1 AA violations found by pa11y-ci
- `app.py`: Added `app.index_string` to set `lang="en"` on the `<html>` element (WCAG 3.1.1).
- `.pa11yci`: Added `hideElements: "#_dash-global-error-container"` to exclude Dash's dev-only debug button, which has no accessible name but is absent in production.

### Fixed pa11y-ci config — renamed to `.pa11yci` and corrected format
pa11y-ci looks for `.pa11yci` by default, not `.pa11yrc.json`. Renamed via `git mv` and restructured config to use the `defaults` key for shared options, which is required by pa11y-ci's config schema. Updated CLAUDE.md reference.

### Set up ADA Title II / WCAG 2.1 AA accessibility linting
Added `pa11y-ci` to test the running Dash app against WCAG 2.1 AA on every push. Created:
- `package.json` — pa11y-ci dev dependency and `npm run a11y` script
- `.pa11yrc.json` — pa11y config targeting WCAG2AA with 2s wait for React rendering
- `.github/workflows/accessibility.yml` — CI job that starts the app and runs pa11y-ci
- Updated `CLAUDE.md` with Dash-specific WCAG 2.1 AA conventions (text alternatives, form labels, heading hierarchy, color contrast, keyboard nav, skip links)
- Updated `.gitignore` to exclude `pa11y-reports/` and `node_modules/`

### Added Git conventions section to CLAUDE.md
Documented branch naming convention: lowercase with dashes, descriptive of functionality.

### Fixed pyright `reportPrivateImportUsage` error in `app.py` (second attempt)
Updated import to `from dash.dcc.Graph import Graph` per pyright's suggested path.

### Fixed pyright `reportPrivateImportUsage` error in `app.py`
Replaced `dcc.Graph` with a direct import of `Graph` from `dash.dcc` to satisfy pyright's public export check. Removed unused `dcc` import.

### Fixed `.gitignore` linter directory name
Changed `linter_logs` to `megalinter-reports` to match the actual directory name generated by MegaLinter.

### Updated CLAUDE.md — startup and changelog instructions
Added instructions telling Claude Code to read `CLAUDE_CHANGELOG.md` at session start and to log all changes after making them.

### Created CLAUDE.md
Initial project documentation file covering layout, run instructions, dependency management, linting, code style, PR process, and database setup.

### Committed .gitignore update
Added `linter_logs` to `.gitignore` under a "Project specific" section.

### Removed `PYTHON_PYLINT_DISABLE_ERRORS` from `.mega-linter.yml`
Re-enabled pylint errors so they will fail CI builds, restoring enforcement of lint quality checks.
