# Part 3 — Design System, Branding, UI Components & Visual Language

## 20. Design Philosophy

The UI should feel like a premium software product (Apple, Linear, Vercel,
Notion, Arc Browser, Raycast quality). Communicate quality through
simplicity, consistency, and motion — not visual clutter. Never resemble
Bootstrap dashboards, admin templates, generic chatbot clones, heavy Material
Design, or hackathon projects. Every screen should feel handcrafted.

## 21. Brand Identity

**Name:** Mistral AI Workspace
**Personality:** Modern, intelligent, premium, fast, minimal, professional,
trustworthy, developer-friendly. It should feel like a professional
developer tool, not a consumer app.

## 22. Design Keywords

Minimal · Elegant · Calm · Clean · Airy · Responsive · Fast · Modern ·
Professional · High Contrast · Pixel Perfect

## 23. Color System

### Light Theme

| Token | Value |
|---|---|
| Background | `#FFFFFF` |
| Secondary Background | `#FAFAFA` |
| Card | `#FFFFFF` |
| Border | `#E5E7EB` |
| Primary (text) | `#111827` |
| Secondary Text | `#6B7280` |
| Accent | `#2563EB` |
| Success | `#22C55E` |
| Warning | `#F59E0B` |
| Error | `#EF4444` |

### Dark Theme

| Token | Value |
|---|---|
| Background | `#09090B` |
| Secondary Background | `#111827` |
| Card | `#18181B` |
| Border | `#27272A` |
| Primary Text | `#F9FAFB` |
| Secondary Text | `#9CA3AF` |
| Accent | `#3B82F6` |
| Success | `#22C55E` |
| Warning | `#FBBF24` |
| Error | `#EF4444` |

### Rules

- No gradients for backgrounds.
- No neon colors.
- Accent color reserved for interactive elements only.
- Subtle shadows only.
- High contrast in both themes.

Implement as CSS variables / Tailwind theme tokens — never hardcode hex
values in component code.

## 24. Typography

**Family:** Geist (primary), Inter (fallback), Geist Mono (code).

| Style | Size |
|---|---|
| Hero | 64px |
| H1 | 48px |
| H2 | 36px |
| H3 | 28px |
| H4 | 22px |
| Body Large | 18px |
| Body | 16px |
| Small | 14px |
| Caption | 12px |

**Weights:** Regular 400 · Medium 500 · SemiBold 600 · Bold 700

## 25. Spacing System

8-point grid: `4, 8, 12, 16, 24, 32, 40, 48, 64, 80, 96, 128`. Never use
arbitrary spacing values — always snap to this scale (Tailwind spacing scale
configured to match).

## 26. Border Radius

| Element | Radius |
|---|---|
| Buttons | 12px |
| Cards | 20px |
| Inputs | 14px |
| Dialogs | 24px |
| Images | 18px |

## 27. Shadows

Only three elevation levels: **Small** (cards), **Medium** (hover), **Large**
(dialogs). Avoid heavy shadows.

## 28. Icon System

Library: **Lucide React**. Sizes: 16 / 18 / 20 / 24 only — icons never exceed 24px.

## 29. Animation System

Library: **Framer Motion**. Durations: 100 / 150 / 250 / 300ms. Easing:
`ease-out`. No bounce.

## 30. Component Library

Every component must be reusable, typed, and composable.

**Button** — variants: Primary, Secondary, Ghost, Outline, Destructive, Link.
Sizes: Small, Medium, Large, Icon. States: Default, Hover, Active, Loading,
Disabled. Loading button shows a spinner + "Uploading..." style label.

**Input** — types: Text, Password, Search, Number. States: Focus, Error,
Disabled, Success.

**Textarea** — used for OCR output / transcript. Features: auto-resize, copy
button, character counter.

**Card** — Title, Description, Content, Footer slots. Hover animation required.

**Badge** — variants: Success, Warning, Error, Info, Neutral.

**Dialog** — used for Help, About, Settings. Must animate smoothly.

**Tooltip** — required on buttons, icons, shortcuts.

**Toast** — notifications (e.g. "Copied", "Downloaded", "Upload Complete",
"Microphone Enabled"), 3-second duration.

## 31. OCR Components

- **Upload Card** — drag area, upload button, file preview, remove button.
- **Progress Component** — stages: Uploading → Reading → Extracting →
  Formatting → Done, animated progress bar.
- **OCR Result** — Markdown / Plain Text tabs, copy, download, word count,
  character count.

## 32. Speech Components

- **Microphone Card** — Start, Pause, Resume, Stop.
- **Transcript Card** — live streaming text, never waits until recording ends.
- **Statistics Card** — Words, Characters, Duration, Recording Status.

## 33. Shared Components

Navbar, Footer, ThemeToggle, LoadingSpinner, ProgressBar, ErrorBanner,
SkeletonLoader, EmptyState, Modal, ConfirmationDialog, ShortcutHint — all
reusable, all in `components/common` or `components/ui`.

## 34. Empty Illustrations

Simple, minimal line-art only (document icon for OCR, microphone icon for
Speech) — no cartoon artwork.

## 35. Skeleton Loading

Every API request shows skeletons instead of blank areas (block placeholders
for OCR text; animated placeholder lines for transcript).

## 36. Scrollbars

Custom, thin, rounded, theme-matched scrollbar styling.

## 37. Theme System

Light / Dark / System. Instant switching, **no flash on page load**, persist
preference in `localStorage` (read before first paint to avoid FOUC).

## 38. Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| Ctrl+O | Upload file |
| Ctrl+C | Copy result |
| Ctrl+D | Download |
| Space | Start/Stop recording |
| Esc | Close dialog |

Surface shortcuts in tooltips where appropriate.

## 39. Mobile Design

Thumb-friendly, tap targets ≥48px, no horizontal scrolling, sticky bottom
actions where useful, smooth transitions, spacing optimized for small screens.

## 40. UI Quality Checklist

- [ ] Pixel-perfect alignment
- [ ] Consistent spacing (8px grid)
- [ ] No overlapping elements
- [ ] No layout shifts
- [ ] Smooth 60 FPS animations
- [ ] Responsive across all breakpoints
- [ ] Dark mode parity with light mode
- [ ] Accessible focus states
- [ ] Reusable components only, no duplicated UI code
- [ ] Design tokens used consistently
- [ ] Premium visual polish before feature expansion

## Deliverable

A modular design system so future Mistral AI features can be added without
redesigning existing components. Quality bar: could be featured on Product
Hunt / Vercel Showcase.

---
**Author:** Pranjul Rathour
**Designation:** GenAI Engineer
**Organization:** NEXT UPGRAD WEB SOLUTIONS
