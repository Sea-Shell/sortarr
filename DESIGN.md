---
version: alpha
name: sortarr
description: Design system for sortarr - YouTube Subscription Router
colors:
  primary: '#E62117'
  primary-hover: '#CC1E15'
  primary-muted: rgba(230,33,23,0.08)
  link: '#CC1E15'
  link-hover: '#E62117'
  secondary: '#5C5A54'
  tertiary: '#8C8A84'
  muted: '#767676'
  canvas: '#F7F5F0'
  surface: '#FFFFFF'
  surface-2: '#F0EDE8'
  surface-hover: '#EBE8E0'
  on-surface: '#1A1A1A'
  border: rgba(0,0,0,0.08)
  border-hover: rgba(0,0,0,0.15)
  border-focus: rgba(230,33,23,0.4)
  success: '#2E7D32'
  success-bg: rgba(46,125,50,0.06)
  warning: '#E65100'
  warning-bg: rgba(230,81,0,0.06)
  error: '#C62828'
  error-bg: rgba(198,40,40,0.06)
  info: '#1565C0'
  info-bg: rgba(21,101,192,0.06)
typography:
  display-lg:
    fontFamily: '"Fraunces", Georgia, serif'
    fontSize: clamp(1.5rem, 4vw, 2rem)
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: -0.02em
  display-md:
    fontFamily: '"Fraunces", Georgia, serif'
    fontSize: clamp(1.25rem, 3vw, 1.75rem)
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: -0.02em
  display-sm:
    fontFamily: '"Fraunces", Georgia, serif'
    fontSize: clamp(1.125rem, 2.5vw, 1.25rem)
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: -0.01em
  body-lg:
    fontFamily: '"Inter", -apple-system, sans-serif'
    fontSize: clamp(0.9375rem, 2vw, 1rem)
    fontWeight: 400
    lineHeight: 1.5
  body-md:
    fontFamily: '"Inter", -apple-system, sans-serif'
    fontSize: clamp(0.8125rem, 1.5vw, 0.875rem)
    fontWeight: 400
    lineHeight: 1.5
  body-sm:
    fontFamily: '"Inter", -apple-system, sans-serif'
    fontSize: clamp(0.75rem, 1.5vw, 0.8125rem)
    fontWeight: 400
    lineHeight: 1.4
  label-lg:
    fontFamily: '"Inter", -apple-system, sans-serif'
    fontSize: clamp(0.6875rem, 1.25vw, 0.75rem)
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: 0.04em
    textTransform: uppercase
  label-md:
    fontFamily: '"Inter", -apple-system, sans-serif'
    fontSize: clamp(0.625rem, 1.25vw, 0.6875rem)
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: 0.05em
    textTransform: uppercase
  label-sm:
    fontFamily: '"Inter", -apple-system, sans-serif'
    fontSize: clamp(0.5625rem, 1vw, 0.625rem)
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: 0.06em
    textTransform: uppercase
  code:
    fontFamily: '"JetBrains Mono", "Fira Code", monospace'
    fontSize: clamp(0.75rem, 1.5vw, 0.8125rem)
    fontWeight: 400
    lineHeight: 1.5
  code-sm:
    fontFamily: '"JetBrains Mono", "Fira Code", monospace'
    fontSize: clamp(0.6875rem, 1.25vw, 0.75rem)
    fontWeight: 400
    lineHeight: 1.4
rounded:
  sm: 4px
  md: 6px
  lg: 8px
  xl: 12px
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 20px
  2xl: 24px
  3xl: 32px
  4xl: 40px
components:
  button-primary:
    backgroundColor: '#E62117'
    textColor: '#FFFFFF'
    rounded: 6px
    padding: 8px 16px
    typography: label-lg
  button-primary-hover:
    backgroundColor: '#CC1E15'
  button-secondary:
    backgroundColor: transparent
    textColor: '#5C5A54'
    rounded: 6px
    padding: 8px 16px
    border: 1px solid rgba(0,0,0,0.08)
    typography: label-lg
  button-secondary-hover:
    backgroundColor: '#F0EDE8'
    borderColor: rgba(0,0,0,0.15)
    textColor: '#1A1A1A'
  button-ghost:
    backgroundColor: transparent
    textColor: '#8C8A84'
    rounded: 6px
    padding: 8px 12px
    typography: label-lg
  button-ghost-hover:
    backgroundColor: '#F0EDE8'
    textColor: '#1A1A1A'
  button-danger:
    backgroundColor: rgba(198,40,40,0.06)
    textColor: '#C62828'
    rounded: 6px
    padding: 8px 16px
    typography: label-lg
  button-danger-hover:
    backgroundColor: '#C62828'
    textColor: '#FFFFFF'
  button-sm:
    padding: 2px 8px
    typography: label-md
    note: 18px nominal height — use only inside tappable containers (parent provides 44px touch target) or on non-touch interfaces
  button-icon:
    padding: 4px
    minWidth: 44px
    minHeight: 44px
    rounded: 6px
  card:
    backgroundColor: '#FFFFFF'
    rounded: 6px
    padding: 16px 20px
    border: 1px solid rgba(0,0,0,0.08)
  card-hover:
    borderColor: rgba(0,0,0,0.15)
    boxShadow: 0 2px 8px rgba(0,0,0,0.08)
    transform: translateY(-2px)
  stat-card:
    backgroundColor: '#FFFFFF'
    rounded: 6px
    padding: 20px
    border: 1px solid rgba(0,0,0,0.08)
  badge:
    rounded: 4px
    padding: 1px 6px
    typography: label-sm
  badge-success:
    backgroundColor: rgba(46,125,50,0.06)
    textColor: '#2E7D32'
  badge-warning:
    backgroundColor: rgba(230,81,0,0.06)
    textColor: '#E65100'
  badge-error:
    backgroundColor: rgba(198,40,40,0.06)
    textColor: '#C62828'
  badge-info:
    backgroundColor: rgba(21,101,192,0.06)
    textColor: '#1565C0'
  badge-accent:
    backgroundColor: rgba(230,33,23,0.08)
    textColor: '#E62117'
  input:
    backgroundColor: '#F7F5F0'
    textColor: '#1A1A1A'
    rounded: 6px
    padding: 8px 12px
    border: 1px solid rgba(0,0,0,0.08)
    typography: body-md
  input-focus:
    borderColor: rgba(230,33,23,0.4)
  input-placeholder:
    textColor: '#767676'
  run-card:
    backgroundColor: '#FFFFFF'
    rounded: 6px
    padding: 16px 20px
    border: 1px solid rgba(0,0,0,0.08)
  run-card-hover:
    borderColor: rgba(0,0,0,0.15)
    boxShadow: 0 1px 4px rgba(0,0,0,0.04)
  decision-card:
    backgroundColor: '#FFFFFF'
    rounded: 6px
    padding: 12px 20px
    border: 1px solid rgba(0,0,0,0.08)
  decision-card-added:
    borderLeft: 3px solid '#2E7D32'
    backgroundColor: rgba(46,125,50,0.06)
  decision-card-skipped:
    borderLeft: 3px solid '#E65100'
    backgroundColor: rgba(230,81,0,0.06)
  decision-card-error:
    borderLeft: 3px solid '#C62828'
    backgroundColor: rgba(198,40,40,0.06)
  modal:
    backgroundColor: rgba(22,22,24,0.85)
    rounded: 6px
    border: 1px solid rgba(255,0,51,0.1)
    padding: 20px
    backdropFilter: blur(20px)
    maxWidth: 560px
  modal-drawer:
    backgroundColor: rgba(22,22,24,0.95)
    rounded: 6px
    border: 1px solid rgba(255,0,51,0.1)
    padding: 16px
    backdropFilter: blur(20px)
    width: 100%
    maxHeight: 90vh
    overflowY: auto
  sub-card:
    backgroundColor: '#FFFFFF'
    rounded: 6px
    padding: 16px
    border: 1px solid rgba(0,0,0,0.08)
  pipeline-card:
    backgroundColor: '#FFFFFF'
    rounded: 6px
    padding: 20px
    border: 1px solid rgba(0,0,0,0.08)
  toast:
    rounded: 6px
    padding: 8px 16px
    typography: body-sm
  toast-success:
    backgroundColor: rgba(46,125,50,0.06)
    textColor: '#2E7D32'
    borderColor: rgba(46,125,50,0.2)
  toast-error:
    backgroundColor: rgba(198,40,40,0.06)
    textColor: '#C62828'
    borderColor: rgba(198,40,40,0.2)
  toast-warning:
    backgroundColor: rgba(230,81,0,0.06)
    textColor: '#E65100'
    borderColor: rgba(230,81,0,0.2)
  toast-info:
    backgroundColor: rgba(21,101,192,0.06)
    textColor: '#1565C0'
    borderColor: rgba(21,101,192,0.2)
  overflow-menu:
    backgroundColor: '#FFFFFF'
    rounded: 6px
    padding: 4px 0
    boxShadow: 0 4px 16px rgba(0,0,0,0.12)
    border: 1px solid rgba(0,0,0,0.08)
    zIndex: 50
  overflow-menu-item:
    padding: 8px 16px
    typography: body-md
    minWidth: 160px
  overflow-menu-item-hover:
    backgroundColor: '#F0EDE8'
  skeleton:
    backgroundColor: '#F0EDE8'
    rounded: 4px
    minHeight: 14px
  skeleton-card:
    backgroundColor: '#F0EDE8'
    rounded: 6px
    minHeight: 80px
  skeleton-text:
    backgroundColor: '#F0EDE8'
    rounded: 4px
    minHeight: 14px
    width: 60%
  drawer:
    backgroundColor: '#F0EDE8'
    width: 280px
    borderRight: 1px solid rgba(0,0,0,0.08)
    zIndex: 200
  drawer-overlay:
    backgroundColor: rgba(0,0,0,0.5)
    zIndex: 199
---

## Overview

sortarr is a YouTube Subscription Router — an operations tool for engineers who manage YouTube channel subscriptions, pipeline runs, and playlist routing. The design is **editorial-technical**: warm off-white canvas with a sharp red accent, serif display typeface for personality, and monospaced code for data values.

**Audience:** The operator who runs this on a phone between other things. They need glanceable status, fast actions, and a layout that adapts to any screen without losing density or context.

**Emotional response:** Capable but not cold. Like a well-worn tool — it does one job precisely and doesn't get in your way.

## Colors

The palette is warm-neutral with a red accent for energy and action. Status colors carry semantic meaning and include matching background tints for badges and cards.

**VERIFIED contrast ratios (WCAG 2.2 AA):**

| Token pair | Ratio | Level |
|---|---|---|
| `on-surface` (#1A1A1A) on `canvas` (#F7F5F0) | 16.0:1 | AAA |
| `on-surface` (#1A1A1A) on `surface` (#FFFFFF) | 17.4:1 | AAA |
| `secondary` (#5C5A54) on `canvas` (#F7F5F0) | 6.3:1 | AA |
| `tertiary` (#8C8A84) on `canvas` (#F7F5F0) | 3.2:1 | AA (large text) |
| `primary` (#E62117) on `surface` (#FFFFFF) | 4.6:1 | AA |
| `link` (#CC1E15) on `canvas` (#F7F5F0) | 5.1:1 | AA |
| `muted` (#767676) on `surface` (#FFFFFF) | 4.5:1 | AA |
| `muted` (#767676) on `canvas` (#F7F5F0) | 4.2:1 | AA (large text) |
| `success` (#2E7D32) on `surface` (#FFFFFF) | 5.1:1 | AA |
| `error` (#C62828) on `surface` (#FFFFFF) | 5.6:1 | AA |
| `warning` (#E65100) on `surface` (#FFFFFF) | 3.8:1 | AA (large text) |

All ratios computed programmatically from hex values. The `muted` token was raised from #B0ADA6 (2.2:1 FAIL) to #767676 (4.5:1 AA). A `link` token (#CC1E15, 5.1:1 on canvas) now provides the default link color instead of `primary` (#E62117, 4.2:1 on canvas — fails AA for normal text). Links are always underlined to provide a non-color distinguishing cue.

## Typography

Three typefaces, each with a distinct role:

| Role | Face | Weight | Size (fluid) |
|---|---|---|---|
| Display / headings | Fraunces | 700 | `clamp(1.125rem, 2.5vw, 2rem)` |
| UI labels & body | Inter | 400 / 500 / 600 | `clamp(0.5625rem, 1vw, 1rem)` |
| Code & data | JetBrains Mono | 400 / 500 | `clamp(0.6875rem, 1.25vw, 0.8125rem)` |

All sizes use `clamp()` for fluid scaling — no hard pixel values. The scale is designed so that on a 390px phone the smaller end applies, and on a 1440px desktop the larger end applies, with smooth interpolation in between.

## Layout

### Shell (media-query-driven)

sortarr uses a **responsive shell** pattern with three distinct breakpoints, controlled by media queries:

| Breakpoint | Shell mode | Nav | Content margin |
|---|---|---|---|
| `< 640px` (phone) | Full-bleed single column | Drawer overlay | `0` (no sidebar) |
| `640px — 1024px` (tablet) | Condensed sidebar | Icon-only, 64px | `margin-left: 64px` |
| `> 1024px` (desktop) | Full sidebar | Icon + label + badge | `margin-left: 220px` |

**IMPORTANT:** The shell layout (sidebar, .main-content margin, header) uses **media queries**, not container queries. Shell layout is inherently viewport-relative. Container queries are reserved for internal component reflow (see below). Max page width: `1400px`.

**Build-order prerequisite — CSS alias layer first:** The CSS alias layer (§Components → Alias layer + Pre-existing fixes) and the responsive shell both modify the same `:root` block in `ui/index.html`. These must ship **before** the shell refactor — the alias layer adds `--color-*`, `--sp-*`, `--radius-*` and `--font-*` variables and fixes the pre-existing bugs (`--surface-1`, `--red`, etc.). The shell then uses those new variables. If these were parallel tasks, one commit could capture the other's unfinished work in the single-file `<style>` block. **Sequence: (1) Alias layer + pre-existing fixes, then (2) Responsive shell.** Do not interleave.

### Internal layout (container-query-driven)

Inside pages, specific grid containers use `container-type: inline-size` for internal reflow independent of viewport:

| Container element | Selector | Breakpoints |
|---|---|---|
| Stat grid | `.stat-grid` | 1-col < 300px, 2-col 300–600px, 4-col > 600px |
| Comparison grid | `.comparison-grid` | 1-col < 500px, 2-col ≥ 500px |
| Pipeline cards container | `.page.active#pipelines` | (no container query — cards stack vertically) |
| Run cards container | `.page.active#runs .runsList` | (no container query — cards stack vertically) |

The existing `grid-template-columns: repeat(auto-fill, minmax(200px, 1fr))` on `.stat-grid` already provides implicit responsive columns and is sufficient. If container queries are added, they should be a **supplement** to this, not a replacement — e.g., overriding to 1-col below a container width of 300px.

**Migration note:** The existing breakpoint at `768px` (collapsed sidebar 56px) moves to the new `640px` boundary. Content at 641–767px that was "tablet" stays "tablet". Content at 481–639px moves from "tablet" to "phone" — these widths must now show the drawer (not the collapsed sidebar). The existing `480px` breakpoint (stat-grid 1-col) is subsumed by `< 640px`.

### Navigation

- **Phone (<640px):** Hamburger icon in the top bar opens an overlay drawer (darkened background, 280px drawer from the left). The sidebar element slides in from the left. Tapping outside closes it. The active page is highlighted with a red left bar. Escape closes it. Drawer z-index: 200, overlay z-index: 199.
- **Tablet (640–1024px):** Sidebar collapses to 64px icon-only. No label text visible. The sidebar is always visible, no drawer.
- **Desktop (>1024px):** Full 220px sidebar with labels, SVG nav icons, and status indicators.

### Empty states

Every list view shows a meaningful empty state with a short message and a primary action button. No bare "No data" or empty containers with no feedback.

## Elevation & Depth

Low-contrast, almost flat. Cards and surfaces use subtle borders (`rgba(0,0,0,0.08)`) rather than heavy box-shadows. Hover states gently lift with `translateY(-2px)` and a soft shadow. The only elevated elements are modals (backdrop blur), toasts (fixed position, no shadow), and the overflow menu (document-level shadow).

**z-index layers:**
- `1` — content and sticky headers
- `20` — dropdowns, autocomplete lists
- `50` — overflow menus
- `99` — sidebar overlay (backdrop)
- `100` — sidebar
- `199` — drawer overlay (phone)
- `200` — modals, drawer
- `300` — toasts

## Shapes

Border radii are small and consistent: `4px` for tags and micro-elements, `6px` for cards and buttons, `8px` for stat cards on mobile, `12px` for hero cards.

## Icons

### Loading mechanism

Phosphor icons loaded via CDN script tag in `<head>`:
```html
<script src="https://unpkg.com/@phosphor-icons/web@2.1.1"></script>
```
This registers the `<i class="ph ph-{name}">` element syntax and the `ph-` CSS icon font. No build step required. Icons are SVG-in-font, respect `currentColor`, and are accessible by default when paired with `aria-hidden="true"`.

### Icon sizing

- Navigation icons: `font-size: 1.25rem` (20px)
- Inline action icons (buttons): `font-size: 1rem` (16px) — inherits button text size
- Search icon: `font-size: 1rem`
- Overflow menu items: `font-size: 1rem` (16px)

### Nav icon mappings

| Nav item | Old HTML entity | Phosphor icon |
|---|---|---|
| Dashboard | `&#9632;` (▪) | `ph-grid-four` |
| Runs | `&#8635;` (↻) | `ph-clock-counter-clockwise` |
| Subscriptions | `&#9776;` (☰) | `ph-list-bullets` |
| Pipelines | `&#8594;` (→) | `ph-arrow-elbow-down-right` |
| Settings | `&#9881;` (⚙) | `ph-gear-six` |

### Action icon mappings

| Action | Old entity | Phosphor icon |
|---|---|---|
| Run pipeline | `&#9654;` (▶) | `ph-play` |
| Dry run | `&#9678;` (◎) | `ph-play-circle` |
| Compare | `&#8646;` (⇆) | `ph-arrows-left-right` |
| Watch video | `&#9654;` (▶) | `ph-play` |
| Move up | `&#9650;` (▲) | `ph-caret-up` |
| Move down | `&#9660;` (▼) | `ph-caret-down` |
| Search | `&#128269;` (🔍) | `ph-magnifying-glass` |
| Hamburger menu | `&#9776;` (☰) | `ph-list` |
| Close | (none used) | `ph-x` |
| Add / Plus | (rendered as `+`) | `ph-plus` |
| Check / Selected | `&#10003;` (✓) | `ph-check` |

### HTML entity → icon migration

The 17 HTML entity icon instances across the SPA are replaced one-for-one. Each icon element gets `aria-hidden="true"` (decorative) and the parent button/link carries the accessible label. Example before/after:

```html
<!-- Before -->
<span class="nav-icon" aria-hidden="true">&#9632;</span> Dashboard
<!-- After -->
<i class="nav-icon ph ph-grid-four" aria-hidden="true"></i> Dashboard
```

## Components

### CSS Variable Naming & Aliasing

This design system introduces a **CSS custom property alias layer** that coexists with existing variables. The existing variables (`--space-1`, `--accent`, `--canvas`, etc.) remain unchanged — over 200 CSS rules reference them. The alias variables below are ADDED alongside existing ones so new code can use DESIGN.md token names.

**⛔ DO NOT implement this in parallel with the responsive shell (S1).** Both modify the same `:root` block in `ui/index.html`. The alias layer + pre-existing fixes must ship **first** (see §Layout → Shell → Build-order prerequisite), then the responsive shell consumes the new variables.

```css
:root {
  /* ── Semantic color aliases ── */
  --color-primary: var(--accent);            /* #E62117 */
  --color-primary-hover: var(--accent-hover);/* #CC1E15 */
  --color-primary-muted: var(--accent-muted);
  --color-link: #CC1E15;                     /* darker than primary for AA on canvas */
  --color-link-hover: var(--accent);         /* #E62117 */
  --color-canvas: var(--canvas);             /* #F7F5F0 */
  --color-surface: var(--surface);           /* #FFFFFF */
  --color-surface-2: var(--surface-2);       /* #F0EDE8 */
  --color-surface-hover: var(--surface-hover);
  --color-on-surface: var(--text-primary);   /* #1A1A1A */
  --color-secondary: var(--text-secondary);  /* #5C5A54 */
  --color-tertiary: var(--text-tertiary);    /* #8C8A84 */
  --color-muted: #767676;                    /* FIXED: was #B0ADA6 (2.2:1 FAIL) */
  --color-border: var(--border);
  --color-border-hover: var(--border-hover);
  --color-border-focus: var(--border-focus);
  --color-success: var(--added);             /* #2E7D32 */
  --color-success-bg: var(--added-bg);
  --color-warning: var(--skipped);           /* #E65100 */
  --color-warning-bg: var(--skipped-bg);
  --color-error: var(--error);               /* #C62828 */
  --color-error-bg: var(--error-bg);
  --color-info: var(--info);                 /* #1565C0 */
  --color-info-bg: var(--info-bg);

  /* ── Spacing aliases (keep existing --space-1..8) ── */
  --sp-xs: var(--space-1);   /* 4px */
  --sp-sm: var(--space-2);   /* 8px */
  --sp-md: var(--space-3);   /* 12px */
  --sp-lg: var(--space-4);   /* 16px */
  --sp-xl: var(--space-5);   /* 20px */
  --sp-2xl: var(--space-6);  /* 24px */
  --sp-3xl: var(--space-7);  /* 32px */
  --sp-4xl: var(--space-8);  /* 40px */

  /* ── Radius aliases ── */
  --radius-sm: 4px;
  --radius-md: var(--radius);  /* 6px */
  --radius-lg: 8px;
  --radius-xl: 12px;

  /* ── Font aliases ── */
  --font-display: "Fraunces", Georgia, serif;
  --font-ui: "Inter", -apple-system, sans-serif;
  --font-mono: "JetBrains Mono", "Fira Code", monospace;
}
```

### Pre-existing CSS variable fixes

The following CSS variables are referenced in existing CSS but were **never defined** — they must be added during the responsive shell implementation. These are pre-existing bugs, not new issues, but this spec is the right time to fix them:

| Undefined variable | Used in | Fix (map to) |
|---|---|---|
| `--surface-1` | `.card` background (line 212) | `var(--surface)` — typo fix |
| `--surface-3` | `.config-tab.active`, `.settings-tab.active` (lines 481, 503) | `var(--surface-hover)` |
| `--hover-bg` | (not found — check during implementation) | Remove or alias |
| `--red`, `--red-muted` | `.toast.error`, `.error-state`, `.del-entry:hover` | `var(--color-error)`, `var(--color-error-bg)` |
| `--green`, `--green-muted` | `.toast.success` | `var(--color-success)`, `var(--color-success-bg)` |
| `--amber`, `--amber-muted` | `.toast.warning` | `var(--color-warning)`, `var(--color-warning-bg)` |

### CSS class → DESIGN.md token mapping

The existing SPA uses CSS class names. These are the mapping to DESIGN.md frontmatter tokens:

| Existing CSS class | DESIGN.md token | Notes |
|---|---|---|
| `.btn-primary` | `button-primary` | |
| `.btn-secondary` | `button-secondary` | |
| `.btn-ghost` | `button-ghost` | |
| `.btn-danger` | `button-danger` | |
| `.btn-sm` | `button-sm` | |
| `.btn-icon` | `button-icon` | New: min 44×44px for tap targets |
| `.card` | `card` | |
| `.card-hover` | `card-hover` | |
| `.stat-card` | `stat-card` | |
| `.badge` | `badge` | |
| `.badge-completed`, `.badge-ok` | `badge-success` | Rename |
| `.badge-running`, `.badge-run` | `badge-warning` | Rename |
| `.badge-failed`, `.badge-error` | `badge-error` | Rename |
| `.badge-info` | `badge-info` | Keep name |
| `.badge-accent` | `badge-accent` | Keep name |
| `.run-card` | `run-card` | |
| `.run-card:hover` | `run-card-hover` | |
| `.decision-card` | `decision-card` | |
| `.decision-card.added` | `decision-card-added` | |
| `.decision-card.skipped` | `decision-card-skipped` | |
| `.decision-card.error` | `decision-card-error` | |
| `.modal-overlay` | (shell element) | Keep |
| `.modal` | `modal` | |
| `.toast` | `toast` | |
| `.toast.error` | `toast-error` | |
| `.toast.success` | `toast-success` | |
| `.toast.warning` | `toast-warning` | |
| `.sub-card` | `sub-card` | |
| `.pipeline-card` | `pipeline-card` | |
| `input`, `select`, `textarea` (elements) | `input` | |
| `.sidebar` | (shell element) | Keep |
| `.sidebar-logo` | (shell element) | Keep |
| `.sidebar-nav` | (shell element) | Keep |
| `.sidebar-footer` | (shell element) | Keep |
| `.main-content` | (shell element) | Keep |
| `.main` | (shell element) | Keep |
| `.header` | (shell element) | Keep |
| `.app-shell` | (shell element) | Keep |

**Migration strategy:** Keep all existing CSS class names. Rename badge classes (`.badge-completed` → `.badge-success`, `.badge-running` → `.badge-warning`, `.badge-failed` → `.badge-error`) after updating all JS references. Add DESIGN.md tokens as CSS custom properties (see aliases above) for new code. No wholesale class rename — old names continue working but new components use token-based class names.

### Button variants

Four variants (primary / secondary / ghost / danger) + size modifier (sm). Disabled state is `opacity: 0.5; cursor: not-allowed` on all. Hover states use color transitions at 120ms. The new `button-icon` variant provides 44×44px minimum tap targets for icon-only buttons (e.g., the mobile menu toggle, close buttons). `button-sm` is only appropriate inside already-tappable containers or on non-touch interfaces — its nominal padding yields ~18px height, below the 44px minimum touch target.

### Cards

Seven card types (stat, run, decision, sub, pipeline, skeleton, generic) each with consistent border/padding/radius. Hover states use the `card-hover` tokens where applicable. Skeleton card variants exist for loading states — they use a shimmer/pulse animation (see Animation section).

### Badges

Five semantic colors (success, warning, error, info, accent). All badges are inline-flex with uppercase letter-spaced text. The existing `.badge-completed` and `.badge-ok` classes are renamed to `.badge-success`; `.badge-running` and `.badge-run` to `.badge-warning`; `.badge-failed` and `.badge-error` to `.badge-error`.

### Modals

- **Desktop/tablet:** Centered overlay with backdrop blur (`backdrop-filter`). Focus-trapped. Closed by Escape or backdrop click. Max-width 560px.
- **Phone (<640px):** The pipeline editor modal becomes a full-screen drawer (`modal-drawer` tokens). Max-height 90vh with overflow-y scroll. Slide-up animation. Close button at top-right of the drawer content area. Backdrop click closes. Focus-trapped.

### Toasts

Fixed top-right on desktop, top-center on mobile. Auto-dismiss after 4s. Four types: success, error, warning, info — each with defined `toast-{type}` color tokens. The toast positioning on mobile switches from `right: var(--sp-lg)` to `left: 50%; transform: translateX(-50%)`.

### Pipeline overflow menu

On mobile, the 7-action button row on pipeline cards compresses to 2 primary buttons (Run, Dry Run) + a vertical overflow (⋮) menu implemented via a toggle. The overflow menu exposes Edit, Del, Move Up, Move Down. Desktop keeps all 7 buttons visible.

**Behavior:**
- Overflow trigger is a `button-icon` (44×44px) with the `ph-dots-three-vertical` icon
- Clicking toggles the menu open/closed
- The menu is a `position: absolute` dropdown below the trigger, using `overflow-menu` tokens
- Clicking outside or pressing Escape closes it
- Menu items use `overflow-menu-item` tokens with hover state (`overflow-menu-item-hover`)
- Each item includes a Phosphor icon prefix + text label

### Skeleton loading states

Skeleton loading states appear on every async data fetch. Three skeleton variants:

| Variant | Usage | Shape |
|---|---|---|
| `skeleton` | Generic text placeholder | Single horizontal bar, 14px height |
| `skeleton-text` | Multi-line text block | 3 stacked bars of decreasing width (60%, 80%, 40%) |
| `skeleton-card` | Card placeholder | Card-sized rectangle, 80px min-height |

All skeletons use `background-color: var(--color-surface-2)` with a shimmer animation (see Animation). Skeletons display in place of card content during fetch and are replaced atomically once data arrives — no transition, just swap the innerHTML.

## Animation

Animations are minimal and purposeful:

| Animation | Trigger | Duration | Easing | Reduced motion |
|---|---|---|---|---|
| Skeleton shimmer | On mount, loop 2s | 2s | linear | `display: none` |
| Card hover lift | `:hover` | 200ms | ease-out | Transform passes instantly (0.01ms) |
| Page fade-in-up | `showPage()` | 300ms | ease-out | `opacity: 1; transform: none` |
| Modal backdrop | `openModal()` | 200ms | ease-out | `opacity: 1` instantly |
| Toast appearance | `showToast()` | 200ms | ease-out | `opacity: 1` instantly |
| Sidebar collapse | Media query change | 200ms | ease-out | 0.01ms transition |
| Drawer slide-in | `toggleMobileMenu()` | 250ms | ease-out | `transform: translateX(0)` instantly |

All animations respect `prefers-reduced-motion: reduce` per the existing blanket override:
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

## Do's and Don'ts

- ✅ DO use `clamp()` for font sizes — never fixed px for body text
- ✅ DO design for the smallest container first, then expand (container queries supplement, not replace, media queries)
- ✅ DO use the Fraunces accent red for the sortarr logo and primary actions
- ✅ DO maintain 44px minimum tap targets on all interactive elements — use `button-icon` for icon-only actions
- ✅ DO wrap long action bars in overflow menus on mobile (Run + Dry Run visible, rest under ⋮)
- ✅ DO show skeleton/loading states on every async data fetch
- ✅ DO use `var(--color-link)` (#CC1E15) for link text — links must be underlined
- ✅ DO use `var(--color-muted)` (#767676) for placeholder text — old #B0ADA6 failed WCAG
- ✅ DO use the CSS alias layer (`--color-*`, `--sp-*`) for new code; keep existing `--space-N` etc. for backward compat
- ❌ DON'T use the sidebar on phone — use the drawer pattern
- ❌ DON'T stack more than 3 primary actions in a row on any screen
- ❌ DON'T use borders alone to communicate status — always pair with text or icon
- ❌ DON'T animate motion when `prefers-reduced-motion: reduce` is set
- ❌ DON'T gate features behind hover that are critical on mobile
- ❌ DON'T use fixed-width modals on small viewports — prefer full-screen drawers
- ❌ DON'T use `backdrop-filter` inside `position: fixed` elements on iOS without `@supports` fallback
- ❌ DON'T assume `--surface-1` or `--surface-3` exist — they're pre-existing bugs; use `--surface` / `--surface-hover` instead
- ❌ DON'T use `--red`, `--green`, `--amber` — they were never defined; use `var(--color-error)`, `var(--color-success)`, `var(--color-warning)` instead
