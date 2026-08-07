# Mistral AI Workspace — Frontend

Next.js 15 (App Router) + TypeScript + Tailwind CSS v4 + shadcn/ui (Nova
preset: Lucide + Geist) + Framer Motion.

See the full spec in [`../docs/prd/`](../docs/prd/00-index.md), particularly
[04-architecture.md](../docs/prd/04-architecture.md) for the folder structure
and layering rules this app follows.

## Develop

```bash
npm install
copy .env.example .env.local
npm run dev
```

Runs at `http://localhost:3000`. Requires the backend running at the URL in
`NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`).

## Structure

```
app/          routes (App Router)
components/   common/, layout/, ocr/, speech/, settings/, ui/ (shadcn primitives)
hooks/        useOCR, useSpeech, useTheme
lib/          api client, constants, utils
services/     one file per backend capability — the only place that calls lib/api
types/        shared TS types matching backend schemas
```

Components never call `fetch` directly — always Component → Service →
`lib/api.ts` (see PRD §50).
