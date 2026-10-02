# SCMIRN Enterprise Demo Environment

## Goal
Provide a live sales sandbox with realistic sample data and scripted enterprise scenarios.

## Components
1. Backend API with enterprise routes enabled.
2. Frontend command-center panel in platform overview.
3. Demo seed data in `docs/enterprise/demo/sample_city_seed.json`.
4. Executive briefing PDF generation and download path validation.

## Local Run
1. Backend:
```bash
cd src/backend
python -m pytest -q
python wsgi.py
```
2. Frontend:
```bash
cd src/frontend
npm run typecheck
npm run dev
```

## Sales Demo Script
1. Load city health score and risk radar.
2. Run crisis simulation (`EARTHQUAKE + CYBERATTACK`).
3. Run ROI calculator for proposed investments.
4. Generate executive briefing PDF.
5. Trigger connector authorization flow.
6. Trigger kill switch and review preserved services.

## Demo Success Criteria
1. All enterprise endpoints respond with valid payloads.
2. Frontend renders command-center cards without runtime errors.
3. Generated briefing PDF is stored and retrievable.
