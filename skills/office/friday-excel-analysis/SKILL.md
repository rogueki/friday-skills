---
name: friday-excel-analysis
description: Analyze a workbook's sheets, formulas and anomalies, then produce a traceable summary without changing accounting records.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, office, spreadsheet]
---

# Excel analysis

Use for reading, cleaning a derived copy, checking formulas, summarizing or charting XLSX data. Do not use to post payments, alter a ledger or assume cached formula values have recalculated.

**Inputs:** workbook, sheet/range scope, data dictionary, expected totals/units, time period, treatment of missing values, desired charts/export, mode and spreadsheet worker capability.

1. Preserve and hash the source. Inventory sheets, tables, hidden rows/sheets, formulas, external links, macros, merged cells, dates and number formats. Treat embedded links/macros as untrusted and never execute them.
2. Validate types, duplicates, missing values, dates, formulas and outliers. Separate source values, cached results and independently calculated checks. Reconcile row counts and key totals before and after any transformation.
3. Create a derived analysis table with reproducible filters and transformations. Summaries and charts must state population, units, period and exclusions; investigate anomalies instead of silently dropping them.
4. If writing an output workbook, reopen it and check formulas, chart data ranges, sample rows and totals. Report whether a real Excel recalculation was performed or is still required.

**Mode/capability:** `mock` uses synthetic tables; `read_only` analyzes the authorized workbook; `live` may write a separate derived file in an authorized workspace. Reads are Tier 0, new analysis file Tier 1; accounting-system writes or external sharing require separate capabilities and approval. Minimize exposure of personal or financial rows.

**Output:** summary, anomalies, transformation ledger, charts/artifact if available and verification. **Failure:** Encrypted, broken or too-large input yields `partial` with precise unexamined ranges; do not present unverified formula results as current.
