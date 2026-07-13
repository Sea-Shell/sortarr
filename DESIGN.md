---
version: alpha
name: sortarr v2
description: YouTube subscription router with calm, status-first UI

colors:
  primary: "oklch(0.45 0.15 250)"
  primary-dark: "oklch(0.60 0.12 250)"
  success: "oklch(0.75 0.15 145)"
  success-dark: "oklch(0.65 0.12 145)"
  warning: "oklch(0.70 0.15 85)"
  warning-dark: "oklch(0.60 0.12 85)"
  error: "oklch(0.55 0.20 25)"
  error-dark: "oklch(0.50 0.18 25)"
  surface: "oklch(1.0 0 0)"
  surface-dark: "oklch(0.20 0 0)"
  background: "oklch(0.98 0 0)"
  background-dark: "oklch(0.15 0 0)"
  text: "oklch(0.20 0 0)"
  text-dark: "oklch(0.90 0 0)"
  text-muted: "oklch(0.50 0 0)"
  text-muted-dark: "oklch(0.60 0 0)"
  border: "oklch(0.88 0 0)"
  border-dark: "oklch(0.30 0 0)"

typography:
  headline-lg:
    fontSize: "clamp(1.75rem, 2vw + 1rem, 2.5rem)"
    fontWeight: 600
    lineHeight: 1.2
  body-md:
    fontSize: "clamp(0.875rem, 0.5vw + 0.75rem, 1rem)"
    fontWeight: 400
    lineHeight: 1.5
  body-sm:
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.4

rounded:
  sm: "4px"
  md: "6px"
  lg: "8px"
  full: "9999px"

spacing:
  1: "0.25rem"
  2: "0.5rem"
  3: "0.75rem"
  4: "1rem"
  6: "1.5rem"
  8: "2rem"
---

## Overview

sortarr v2 is a YouTube subscription router with a **calm, status-first interface**. The design prioritizes sporadic checking — users glance to confirm runs passed, then optionally drill into subscriptions and video routing decisions.

**Personality:** Calm dashboard you visit, not a cockpit you live in.

## Colors

Light mode uses soft, editorial colors. Dark mode shifts to dark variants with maintained contrast.

**Status colors:**
- Success: Green for passed runs, routed videos
- Warning: Amber for quota 80-95%, filtered videos
- Error: Red for failed runs, authentication issues

**Contrast ratios:** All text ≥ 4.5:1, interactive elements ≥ 3:1 (WCAG AA).

## Typography

System UI stack for native feel. Fluid scaling with `clamp()` for responsive headlines. Three weights: 400 (body), 500 (labels), 600 (headlines).

## Do's and Don'ts

**Do:**
- Use status cards for at-a-glance health checks
- Provide progressive disclosure (summary → detail)
- Keep mobile touch targets ≥ 44px
- Use relative timestamps ("2 hours ago")
- Show loading skeletons, not spinners
- Validate forms on blur, show errors inline

**Don't:**
- Use color alone for status (pair with icon/text)
- Auto-refresh aggressively (30s polling max)
- Make sidebar wider than 240px
- Use modals for navigation
- Animate on `prefers-reduced-motion: reduce`
