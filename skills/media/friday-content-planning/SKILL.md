---
name: friday-content-planning
description: Plan F.R.I.D.A.Y. Content Studio posts for LinkedIn, Instagram, Facebook, TikTok and YouTube with a shared server plan and optional paired Meta targets.
version: 0.2.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, content-studio, media]
---

# friday-content-planning

**Use:** For Content Studio ideas, posting drafts and plan.json. Do not use for automatic publication or unrelated family video production.

**Inputs:** Campaign goal, audience, target platforms, format, message, source rights, dates, review owner and mode.

1. Draft ideas and postings with distinct identifiers, explicit dates and review status. Treat publication as a separate approval-bound operation.
2. Emit `version: 1` with `content` and `postings` in the format validated by `rogue-friday/packages/generated-sdk/src/content-plan.ts`. Each item retains its primary `plattform` and may add `ziele`, an ordered array of distinct targets from `LinkedIn`, `Instagram`, `Facebook`, `TikTok`, `YouTube`. Keep `Instagram` and `Facebook` together only when the user chose both; never infer publication from this selection. Preserve valid states `idee`, `in-arbeit`, `fertig` and `geplant`, `gepostet`, `verpasst`.
3. Treat the owner-only Control API plan as authoritative. Read `GET /api/v1/content-studio/plan` and use its revision with `If-Match` for any approved `PUT`. On HTTP 409, reload and reconcile; never silently overwrite another client. If the server is empty, offer an existing browser plan for explicit review and import while preserving the browser original. Export the server plan before a file import. Never put API tokens in plan.json.
4. Check platform, date and source rights, then show the final schedule and unresolved facts for review.
5. A spoken request such as "Lade eine neue Story hoch" starts by identifying the finished asset and intended accounts. If either is missing, ask concisely. Record the draft and route an actual publication request to the publishing capability only after the accounts and media are ready. Do not request a dashboard checkbox for a voice request.

**Mode and capability:** mock produces a synthetic plan; read_only reviews a supplied plan; live requires authenticated owner dashboard/API access, CSRF for writes and user review. The API is not an implicit Hermes tool. If the host has no trusted read/write binding, provide a draft for manual import. `file.read` and `file.write` are conditional, never assumed installed.

**Output and verification:** Provide the plan, validation result, backup path if created and review status. Verify import in the dashboard before calling it complete.
