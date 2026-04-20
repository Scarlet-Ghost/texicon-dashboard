# Handoff — Role-Based Login Deployed

**Date:** 2026-04-20 (later session)
**Predecessor:** `2026-04-20-role-based-login-handoff.md`
**Status:** Shipped to production. Login gate live at https://texicon-dashboard.streamlit.app.

---

## What happened this session

1. Remote was on HTTPS as `Scarlet-Ghost/texicon-dashboard` but cached GitHub credentials were for the `dona-create` identity → push rejected 403.
2. Switched `origin` to SSH using the `github-personal` Host alias from `~/.ssh/config` (maps to `~/.ssh/id_personal`, the Scarlet-Ghost key).
3. Pushed 18 commits. `main` now matches `origin/main`.
4. Added the `[auth]` secrets block in Streamlit Cloud app settings → Secrets.
5. Initial paste was missing the `[auth]` section header → `st.secrets["auth"]` KeyError surfaced as "Authentication is not configured" banner. Added the header, saved, propagated (~1 min).
6. Hard-refresh → login page renders, both owner and sales credentials authenticate, user reports "working perfectly."

---

## Current state

- **Remote origin:** `git@github-personal:Scarlet-Ghost/texicon-dashboard.git` (SSH). HTTPS is no longer the push path for this repo on this machine.
- **Branch:** `main` clean, up to date with origin.
- **Deployment:** live at https://texicon-dashboard.streamlit.app with the `[auth]` block in Cloud Secrets.
- **Untracked file still present:** `dashboard/.env.profile` at project root — unrelated to this feature, left alone across two sessions.

---

## Credentials (reference)

Stored in two places, both under `[auth]`:

- Local: `dashboard/.streamlit/secrets.toml` (git-ignored)
- Cloud: Streamlit Cloud → App settings → Secrets

| Role  | Email                | Password           |
|-------|----------------------|--------------------|
| Owner | owner@texicon.com    | `gGv9Pa04JBdDwYI4` |
| Sales | sales@texicon.com    | `DUD7Sp0GY4QlnaRb` |

Rotate by editing both locations; changes propagate in Cloud in ~1 minute.

---

## Verification status

- Owner + sales login in production: **confirmed by user.**
- The rest of the Task 10 checklist from the previous handoff (margin-hidden, alert-strip suppression on p4/p5, URL-bypass blocking, logout cleanup, owner-blocked from `/0_Sales_Home`) remains **not explicitly walked through in production**. If CEO demo is imminent, walk it once end-to-end.

---

## Open items

### Still unresolved from prior handoff
- **Sales Home "Active Customers This Month" / "New This Month" show 0** because source data is stale relative to today. Decide: keep as-is (honest) or relabel to "Latest month in data." No action yet.

### Housekeeping
- Decide fate of `dashboard/.env.profile`. Either delete, gitignore, or leave. It has lived untracked across the role-based-login feature without being needed.

### Not in scope (as before)
No per-user accounts, no audit log, no session timeout, no rate-limiting, no forced re-auth on password rotation. Each tab is its own session.

---

## Gotchas for future sessions

1. **Push auth.** `git config user.email` is `don.a@redactedgroup.io` (work identity), but pushes to this repo go through the `Scarlet-Ghost` SSH key. The SSH alias does the right thing; the committer email is cosmetic.
2. **Streamlit secrets require section headers.** TOML keys without a `[section]` header land in the global scope; `st.secrets["auth"]["foo"]` will fail with a KeyError. Always paste the `[auth]` line.
3. **Propagation delay.** Streamlit Cloud Secrets take ~1 minute to propagate. A hard refresh too soon shows the pre-secrets error and looks like a bug.
4. **Private-repo redeploy trick** (from `project_deployment.md` memory): if a new commit doesn't auto-redeploy, flip the repo public then back to private to nudge Cloud. Did not need it this time — Secrets-save alone triggered reboot.

---

## How to resume

If the next session picks up here:

1. `cd /Users/dxp/Desktop/Personal/07_KKP/01_Texicon`
2. Read this handoff + the predecessor handoff for full feature context.
3. If the CEO demo hasn't happened, walk the Task 10 checklist in production.
4. Address the stale-data KPI question on Sales Home.
