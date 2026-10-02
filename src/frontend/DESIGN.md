---
version: alpha
name: SCMIRN public service and staff workspace
description: A source-first civic service prototype with a clearly separated authenticated staff workspace.
colors:
  primary: "#0f172a"
  accent: "#06b6d4"
  secondary: "#8b5cf6"
  success: "#10b981"
  warning: "#f59e0b"
  danger: "#ef4444"
typography:
  sans:
    fontFamily: "Inter, sans-serif"
  display:
    fontFamily: "Plus Jakarta Sans, sans-serif"
  mono:
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, Liberation Mono, Courier New, monospace"
rounded:
  sm: "0.25rem"
  md: "0.5rem"
  lg: "1rem"
spacing:
  section: "3rem"
  page-container: "Bootstrap .container responsive widths"
components:
  button: "Bootstrap buttons plus .btn-primary-civic for the existing primary CTA"
  card: "Bootstrap .card with existing light border and restrained shadow"
  form: "Native labelled controls styled by Bootstrap"
  banner: "Bootstrap .alert with semantic role and text label"
  list: "Bootstrap responsive card/list surfaces for staff cases"
---

# SCMIRN Design System

## Overview

### Creative North Star

The interface should feel like a well-run public service counter: clear signs, a short queue, and a printed route slip that names its source. Use the existing navy and cyan civic palette to distinguish actions and provenance. Do not borrow the visual identity of a government department or imply endorsement.

### Product context and register

- **Audience and primary job:** People looking for a source-supported public-service next step; provisioned staff who need to review bounded tenant case metadata.
- **Target market and evidence:** India is the intended public-service context in `docs/government/PRODUCT_BRIEF.md`. The current UI is English-only. Regional-language translation, local usability review, and native-language legal/service review have not been completed.
- **Usage scene:** Responsive web use on desktop and mobile, including people with limited time or familiarity with agency terminology. Staff actions require a verified session and must work without hover.
- **Register:** Hybrid. `/` is public route guidance; `/labs/*` is explicitly demonstrative; `/staff` is an authenticated operations surface.
- **Memorable signature:** Every route or case is accompanied by a visible provenance or boundary state: verified source, demo label, or explicit unavailability.
- **Restraint:** Plain-language explanations, short forms, visible error recovery, and familiar native controls take precedence over dashboard density and animation.
- **Anti-references:** Avoid government seals, official-looking success marks, fabricated live counts, predictive-risk charts, and consumer chatbot imagery that could imply a real agency channel.
- **Token ownership/runtime mapping:** This file mirrors the runtime, it does not generate CSS. `src/styles/scmirn.css` owns the six custom color properties listed above; Bootstrap supplies standard neutrals, controls, and responsive containers. Fontsource imports and global focus styles live in `src/main.tsx` and `src/index.css`. There is no generated token adapter or automated token drift gate; review changes against those sources.

## Colors

The navy `primary` (#0f172a) anchors headings and high-emphasis controls. Cyan `accent` (#06b6d4) identifies route and navigation emphasis; violet `secondary` (#8b5cf6) is a supporting accent. Green, amber, and red carry success, caution, and error meaning. Keep the same meaning in text and icon labels; color alone never communicates case status or verification. White cards sit on the pale `#f8fafc` page background. Standard Bootstrap borders and text neutrals remain framework-owned rather than becoming a second project palette. Focus uses the visible cyan outline in `src/index.css`.

The staff workspace uses the same light theme as the public site. There is no dark or high-contrast theme switch. Do not use a green badge to imply official acceptance or resolution beyond the API's literal status.

## Typography

Inter is the interface and reading face. Plus Jakarta Sans is used for headings and the existing brand wordmark. Courier New is reserved for technical payloads in the platform demo. Use sentence case, short labels, and explicit status text. Dates use the browser locale until a product-wide localization and timezone policy is approved; no localized language pack is currently configured.

## Layout

Use Bootstrap's responsive `.container` and grid. The public page keeps a broad editorial hero; workspace pages use shorter headings, readable cards, and comfortable separation. On narrow screens, navigation exposes Labs and Staff on a second row, while cards and case controls stack. Long IDs wrap or remain selectable; do not clip an identifier without a full-value path. Keep the global navigation and sticky layers from obscuring keyboard focus. Staff case cards avoid a wide table and remain usable at mobile widths.

Spacing follows the Bootstrap scale already used in the application (`py-5`, `g-3`, `gap-3`). Rounded corners and shadows are restrained; outline and surface contrast carry structure before elevation. Do not add glass blur, animated count-ups, or hover-only information.

## Components

### Foundational visual states

Use native Bootstrap hover, active, disabled, and focus-visible states. Busy controls keep their label or show a short spinner label and prevent duplicate submission. Loading, empty, unavailable, role-forbidden, and network-failure states use visible text with semantic status or alert roles. Reduced motion is the default for decorative animation; new interactions must honor `prefers-reduced-motion`.

### Buttons and actions

Use one primary action per form and outline/secondary actions for retry, refresh, and restart. Never style a sample record action as a public-service submission. Mutation buttons remain disabled while the API request is pending.

### Navigation and data display

The header identifies public guidance, Labs, and Staff separately. Prototype maps, analytics, directory records, and templates live under `/labs/*`; old direct routes redirect into Labs. Staff cases render as labelled cards with category, priority, server-provided status, and only server-approved next transitions. No client-side value substitutes for server authorization.

### Forms and overlays

Use visible labels, native selects, correct autocomplete semantics, and paste-enabled one-time-code input. Auth errors stay inline and generic. A missing CSRF cookie blocks a mutation and asks for a fresh sign-in. Dialogs and route guidance continue using the existing application-owned components; do not add native `alert()` or `confirm()` flows.

### Iconography

The existing Font Awesome solid set is used for decorative icons. Text labels remain present for all important actions and states. Decorative icons are hidden from assistive technology.

### Motion

Routine work is static. Existing animations are nonessential; new status, loading, and case changes use text and do not depend on motion. Respect reduced-motion settings.

### Content and data visualization

Use direct descriptions: “Staff metadata record created,” “Demo,” “Not submitted,” and “Staff authentication is disabled.” Never describe a prototype record as an official complaint, and do not present demo aggregates as measured outcomes or predictions.

## Do's and Don'ts

- **Do:** Keep source verification, Labs status, and staff authentication visible at the point of action.
- **Do:** Use server-returned case status and permitted transitions, then confirm the returned value in the interface.
- **Don't:** Ask for citizen identity, issue narrative, documents, or evidence in the metadata-only staff API.
- **Don't:** imply a live agency feed, filing, legal advice, government affiliation, or verified case outcome.
