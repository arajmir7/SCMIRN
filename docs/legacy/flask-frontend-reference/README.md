# Retired Flask frontend reference

The code in this directory is preserved for historical comparison. The Flask
app factory does not import or register these page routes. `src/frontend` is the
only production UI; Flask serves JSON APIs and uploaded files.

## Archived source

- `web/templates/`, `web/static/css/scmirn.css`, and `web/static/js/scmirn.js`
  contain the original canonical site.
- `web/routes.py` is the former Jinja page router and is no longer registered.
- `inline-flask-app.py` is an orphaned standalone Flask implementation. It has
  no in-repository production entry point and is not used by the app factory.

## React replacements

| Legacy behavior | React replacement | Coverage |
| --- | --- | --- |
| Chat open/close, quick prompts, send and replies | `src/frontend/src/components/assistant/AssistantPanel.tsx` | Playwright homepage/chat test |
| Report modal, previews, multipart submit | `src/frontend/src/components/reports/ReportIssueModal.tsx` | Playwright multipart and focus test |
| Document types, form and draft generation | `src/frontend/src/components/documents/DocumentGeneratorModal.tsx` | Playwright all-types and failure tests |
| Rights analysis and result rendering | `src/frontend/src/pages/HomePage.tsx` | Playwright success and API-error tests |
| Issue map, filters, search, geolocation, layers, donation and directions | `src/frontend/src/components/map/CivicIssueMap.tsx` and `src/frontend/src/services/geocoding.ts` | Playwright map filter/search/funding test |
| Home page pillar actions | `src/frontend/src/pages/HomePage.tsx` | Browser route and assistant tests |
| Offices, tracker, analytics and documents routes | `src/frontend/src/pages/` | Playwright route, API data and refresh tests |

The newsletter CTA had no legacy submit handler or backend API, so it remains a
non-submitting control. The advanced document download API is not implemented;
the platform workspace reports that backend response when requested.

## Incomplete React placeholders

`src/frontend/src/features/chat/components/FIRChat.tsx` and
`src/frontend/src/features/emergency/components/EmergencyBanner.tsx` are
zero-byte, unreferenced placeholders. They have no behavior and are not
reachable through the migrated routes; they are not represented as completed
features.
