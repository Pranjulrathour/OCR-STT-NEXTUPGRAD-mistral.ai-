# ADR 0003: Allow any localhost port via CORS regex, but only in `local` environment

## Context

`CORS_ORIGINS` required an exact origin match (PRD §64/§93 — CORS enabled
only for explicitly allowed origins). In real usage, `next dev` picks a
random port whenever 3000 is already taken (a second project, a stray
process, etc.), and the mismatch surfaced in the UI as "Connection lost.
Check your network and try again." — indistinguishable from a real network
failure, because a CORS-blocked response looks like a generic network error
to `fetch`. The user hit this on first real-world test (frontend on 3001,
backend only allowing 3000).

## Decision

In `backend/app/middleware/cors.py`, when `ENVIRONMENT=local`, add
`allow_origin_regex` matching `http(s)://(localhost|127.0.0.1)(:\d+)?` in
addition to the explicit `CORS_ORIGINS` list. `staging`/`production` are
unaffected — they still require an exact origin in `CORS_ORIGINS`.

## Consequences

- **Why:** a developer's own machine choosing which port to bind to isn't a
  cross-origin security boundary worth enforcing — the port is already
  fully within the same trust domain (localhost). Enforcing an exact match
  there is friction with no real security payoff.
- Staging/production keep the exact-match allowlist — this relaxation is
  environment-scoped, not a blanket loosening of the CORS policy.
- If a future `local`-env bug is CORS-shaped, remember this regex is now in
  play — check `Disallowed CORS origin` in the backend log to confirm
  whether a request is even reaching the regex check.

## Alternatives Considered

- **Tell the user to manually add every port to `CORS_ORIGINS`.** Rejected:
  this is exactly the friction that caused the bug report — it doesn't
  scale to "whatever port happens to be free today."
- **Force the frontend dev server to a fixed port, failing if taken.**
  Rejected: turns a harmless port conflict into a hard failure instead of
  Next's normal graceful fallback.

---
**Author:** Pranjul Rathour
**Designation:** GenAI Engineer
**Organization:** NEXT UPGRAD WEB SOLUTIONS
