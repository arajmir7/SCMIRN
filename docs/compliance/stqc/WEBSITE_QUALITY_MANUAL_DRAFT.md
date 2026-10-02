# Website quality manual — draft

## Purpose and scope

SCMIRN is a civic guidance application. Its public website must distinguish internal records and generated drafts from official government services. This draft defines expected content, accessibility, security, lifecycle and release checks. It is not yet approved by a website quality owner.

## Content lifecycle

- Every public service/legal claim must have owner, evidence source, reviewer, effective/review date, next review date and retirement rule.
- Stale or uncertain official source content is removed from routing and marked unavailable.
- Metrics include definition, period, source, denominator and independent validation; otherwise they are not published.
- Demo/simulated outputs carry visible demo labels and are not mixed with live citizen or government records.
- Privacy, terms, accessibility, help/contact, grievance and security policy pages require approved owner and version.

## Quality/release checklist

- Correct page metadata, navigation, search and responsive behavior.
- Keyboard and assistive technology support; text alternatives for maps/charts/documents; zoom/reflow and reduced motion.
- Broken-link, markup/style, spell/content, accessibility and security scans.
- Approved versioned APIs, data schemas, retention, privacy notice, production secret/configuration and deployment.
- Restore/rollback evidence, monitoring and incident contacts.
- Final release report names tested artifact digest, outcomes, open risks and accountable approver.

## Current status

The canonical frontend typecheck/build and selected browser suite pass locally. There is no full accessibility report, content ownership register, production restore, approved quality manual or external audit evidence. Approval remains pending.
