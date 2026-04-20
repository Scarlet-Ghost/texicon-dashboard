# 2026-04-21 Evening — UI/UX Audit Handoff

## What shipped this session

Commit `d81e5c7` on `main`:
- TEXICON wordmark 16→24px
- Log out moved into topbar card (right side, via `.tx-logout-slot`)
- Theme toggle moved to fixed bottom-left pill (`.tx-theme-fab`)
- "Logged in as Owner" duplicate row removed (`user_chip()` → no-op)
- Nav hover centered under labels
- Added missing legacy CSS: `.breadcrumb`, `.bc-*`, `.alert-strip*`, `.page-title`, `.page-subtitle` (they were emitted by `drawers.py` but undefined after v9 — that's why breadcrumb and alert strip rendered plain)

Files: `dashboard/components/theme.py`, `drawers.py` (render_top_bar only), `auth.py` (user_chip stubbed).

## User's verdict

> "button placement are shit. layout of buttons are shit. things are all over the place."

Translation: incremental fixes aren't cutting it. User wants a multi-perspective audit before any more code.

## Next session plan — DO NOT START CODING

Spawn **5 agents in parallel** (single message, 5 Agent tool calls). Suggested roles:

1. **Visual hierarchy auditor** — are the right things prominent? Is TEXICON competing with the page title? Do KPI hero cards pull the eye? Walk every page.
2. **Button placement / interaction auditor** — every button on every page: position, grouping, size consistency, affordance. Specifically audit: Log out, theme toggle, Reset, Full Period / Q1 2025 / Q1 2026 / Custom period pills, More Filters expander, action button row, tab switchers. Where do hands go? Where do they land instead?
3. **Layout grid / spacing auditor** — column widths, vertical rhythm, card gutters, alignment across pages. Is there an actual grid or just freestyle? Compare Executive vs Revenue vs Cash vs Reconnect.
4. **CEO-demo critic** — pretend you're the owner showing this to a bank. What looks cheap? What looks unfinished? What would make them trust the numbers less?
5. **Benchmark auditor** — compare against Linear, Stripe, Airbnb dashboards, Vercel, Metabase. Where does Texicon feel like a Streamlit template vs a real product?

Each agent should produce a ranked punch list of concrete fixes with file paths. Do NOT merge into one consensus plan — surface disagreements.

After all 5 report back: consolidate findings, present to user, let user pick which fixes to ship. Then code.

## Suggested agent prompt skeleton

```
You are a [ROLE]. Audit the Texicon Streamlit dashboard at
/Users/dxp/Desktop/Personal/07_KKP/01_Texicon.

Live: https://texicon-dashboard.streamlit.app (owner login in st.secrets,
user will share if needed)

Walk every page (app.py + pages/1-6). Focus: [ROLE-SPECIFIC FOCUS].

Read theme.py to understand the design tokens. Read drawers.py for
chrome components. Do NOT propose changes to business logic or data.

Deliverable: ranked punch list. Each item = one concrete issue + file
path + suggested fix. Rank by impact on CEO-demo perception. Under 400
words. Be opinionated — disagreement with other auditors is fine.
```

## Guardrails

- No emojis in any UI output (locked preference).
- V6 Linear-style: mono + 1 emerald accent, Inter body, borderless cards, 8px grid.
- `₱` peso glyph stays.
- Don't re-introduce `<a href="?...">` controls — they drop the WebSocket session.
- Use `command git` for commits (user's zsh wrapper breaks non-interactively).

## Open carry-overs from v9 QA (still unshipped)

- Serif treatment on page titles (Georgia token exists, not wired)
- Product question: alert-strip only on Executive, not sub-pages?

## Live state

- Branch: `main`
- HEAD: `d81e5c7`
- Streamlit Cloud: auto-rebuilds from main push
