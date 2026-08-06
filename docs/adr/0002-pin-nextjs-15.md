# ADR 0002: Pin Next.js to the 15.x line, not `latest`

## Context

The PRD (`docs/prd/04-architecture.md` §43) explicitly specifies "Next.js 15
(App Router)". Running `create-next-app@latest` at scaffold time resolved to
Next 16.3.0, whose own generated `AGENTS.md` warns: "This is NOT the
Next.js you know... breaking changes... may all differ from your training
data."

## Decision

Scaffolded with `create-next-app@15.5.22` (the latest patch on the 15.x
line) instead of `@latest`.

## Consequences

- **Why:** the PRD's version pin is explicit, not incidental, and the tool
  the newer major version ships for itself flags exactly the risk we'd be
  taking on by ignoring that pin mid-scaffold.
- `npm audit` flags 3 high-severity CVEs (in `postcss`/`sharp`, both
  transitive Next.js dependencies) that are only fixed by upgrading to
  Next 16. Documented and mitigated in `docs/security.md` rather than
  silently accepted — the affected code paths (arbitrary CSS/image
  processing) aren't reachable through this app's own upload flow.
- Revisit this pin if the PRD is updated to allow Next 16, or when a Next
  15.x patch backports the CVE fixes (check `npm audit` after any
  `npm update` inside the 15.x range).

## Alternatives Considered

- **Use `@latest` (Next 16).** Rejected: contradicts an explicit PRD
  requirement without asking first, and 16 is new enough that its own
  tooling flags itself as a breaking change from what most training data
  and documentation assumes.
- **Ignore the CVEs silently.** Rejected: CLAUDE.md's security bar requires
  documenting known residual risk, not asserting a clean bill of health.

---
**Author:** Pranjul Rathour
**Designation:** GenAI Engineer
**Organization:** NEXT UPGRAD WEB SOLUTIONS
