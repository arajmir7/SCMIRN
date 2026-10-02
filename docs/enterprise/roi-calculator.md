# SCMIRN Enterprise ROI Calculator

> **Status (2026-10-01): scenario template only.** Inputs must be supplied and validated by finance/operations owners. No measured SCMIRN loss reduction, savings, adoption, payback or ROI is established. The listed enterprise API is a demo route and is disabled by the production readiness gate.

## Purpose
Support procurement teams with transparent cost-benefit modeling for resilience investments.

## Model Inputs
1. Baseline annual losses:
- infrastructure failures
- emergency response overruns
- legal/compliance penalties
2. Investments:
- CAPEX
- annual OPEX
- expected loss reduction percentage
- implementation timeline
3. Financial assumptions:
- horizon in years
- discount rate

## Outputs
1. Combined prevented losses.
2. Net annual benefit.
3. Payback period.
4. ROI percentage.
5. NPV for procurement committee review.

## Tooling
1. API endpoint: `POST /api/v1/enterprise/executive/roi-calculate`
2. Spreadsheet template: `docs/enterprise/tools/roi_calculator_template.csv`

## Procurement Workflow
1. Populate baseline loss values from finance and operations.
2. Add candidate investment scenarios.
3. Compare `net_benefit_annual_inr`, `payback_years`, and `npv_inr`.
4. Attach output to approval memo and executive briefing.
