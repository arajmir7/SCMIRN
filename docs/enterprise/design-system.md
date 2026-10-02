# SCMIRN Enterprise UI/UX Design System

> **Status (2026-10-01): design guidance, not accessibility certification.** The canonical React site’s current visual composition is preserved. WCAG/GIGW conformance, screen-reader behavior and full-route keyboard/accessibility audits remain unverified; token values and dashboard patterns below are recommendations for future workspaces.

## Design Goals
1. Executive readability in under 10 seconds for critical screens.
2. High-contrast, accessibility-first interaction defaults.
3. Component consistency across war room, operations console, and citizen app.

## Design Tokens
```css
:root {
  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --color-border: #e2e8f0;
  --color-text: #0f172a;
  --color-text-muted: #475569;
  --color-primary: #0ea5e9;
  --color-success: #16a34a;
  --color-warning: #d97706;
  --color-danger: #dc2626;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --shadow-card: 0 14px 35px rgba(15, 23, 42, 0.06);
  --spacing-2: 0.5rem;
  --spacing-4: 1rem;
  --spacing-6: 1.5rem;
  --spacing-8: 2rem;
}
```

## Typography
1. Primary UI: Inter (existing system consistency).
2. Numeric/KPI emphasis: tabular numerals for stable metric scanning.
3. Hierarchy:
- H1: executive page headline.
- H2: capability section.
- H3: functional card title.
- Body: concise operational explanations.

## Core Components
1. KPI Tile
- Label, current value, trend delta, band.
2. Risk Node Table/Card
- Risk type, district, 7/30/90 forecast.
3. Scenario Console
- JSON payload editor + action runner + structured output viewer.
4. Connector Card
- Suite, product, auth profile, capabilities.
5. Incident Action Panel
- Kill switch controls, isolated nodes, preserved services.

## Accessibility Guidelines
1. WCAG 2.1 AAA target for all enterprise dashboards.
2. Keyboard-only navigation for every command action.
3. Minimum 4.5:1 contrast for body text and 7:1 for critical indicators.
4. ARIA labels for control groups and output panels.
5. Screen-reader friendly ordering: heading > status > actions > details.

## Motion and Feedback
1. Use only meaningful transitions for state updates.
2. Loading feedback must be explicit (`Loading...`, `Running...`, `Generating...`).
3. Error states are persistent until user dismissal or successful retry.

## Responsive Rules
1. Desktop: three-column overview layout.
2. Tablet/mobile: single-column stacked cards.
3. JSON and console panels keep scrollable containers with fixed max heights.
