# Security

## Threat model summary

| Asset | Threat | Mitigation |
|---|---|---|
| `MISTRAL_API_KEY` | Leaked to client / logs | Never sent to frontend (backend-only env var); never logged (PRD §89); frontend has zero knowledge of it |
| Uploaded files (OCR) | Malicious/oversized upload, path traversal via filename | Extension + MIME allowlist, 20MB cap, filename sanitized before use (`app/utils/file.py`), never persisted to disk |
| Uploaded audio (Speech) | Oversized upload, empty stream | Size cap, empty-buffer rejection before any Mistral call |
| CORS | Cross-origin abuse | `CORS_ORIGINS` allowlist, no wildcard in production |
| Error responses | Stack trace / internal detail leakage | All exceptions mapped to the standard `{success:false, message}` envelope (PRD §80/§96); unhandled exceptions logged server-side only |

## Secrets handling

- `MISTRAL_API_KEY` lives only in `backend/.env` (gitignored) or the
  deployment platform's secret store — never committed, never in
  `docker-compose.yml` literals (passed through as `${MISTRAL_API_KEY}`).
- `.env.example` files (frontend and backend) are checked in with no real
  values, documenting what's required.

## What is deliberately NOT implemented (see PRD §1 non-goals)

No auth, no accounts, no database — there is no user data at rest to
protect beyond the transient uploaded file/audio, which is processed
in-memory and never persisted to disk.

## Known residual risk

`frontend/package.json` pins Next.js to the 15.x line per the PRD's explicit
version requirement. `npm audit` flags high-severity CVEs in `postcss`/`sharp`
that are only fixed by upgrading to Next 16 (a breaking change outside this
PRD's scope). Mitigation: the app never routes user-uploaded files through
`next/image`/`sharp` — uploads go straight to the backend as raw bytes — so
the image-processing CVE surface isn't reachable through this app's own code
paths. Revisit if the PRD's Next version pin is ever relaxed.

---
**Author:** Pranjul Rathour
**Designation:** GenAI Engineer
**Organization:** NEXT UPGRAD WEB SOLUTIONS
