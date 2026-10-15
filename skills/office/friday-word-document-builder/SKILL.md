---
name: friday-word-document-builder
description: Build a branded DOCX from approved content and template with styles, tables, page furniture and checked export.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, office, docx]
---

# Word document builder

Use when approved text needs a structured Word deliverable. Do not use for fact finding, report argumentation or a simple plain-text answer.

**Inputs:** approved content, brand/template DOCX, heading hierarchy, table and image assets, title/metadata, target Word/PDF versions, mode and document worker/render capabilities.

1. Inspect the template's styles, section breaks, margins, headers/footers, numbering and font availability. Preserve the original and identify unsupported controls such as tracked changes, fields or complex content controls.
2. Build a separate document using heading styles, semantic tables, alt text where available, caption/source references, consistent headers/footers and page numbers. Generate or refresh the table of contents only with a tool that supports field updates; otherwise mark it pending.
3. Render every page and inspect page breaks, widows/orphans, overflow, table splits, contrast and missing glyphs. Export PDF only if a confirmed local conversion capability exists and compare page counts/content.
4. Reopen the DOCX; verify required sections and links, report template deviations and any field that requires manual Word refresh.

**Mode/capability:** `mock` yields a sample layout spec; `read_only` checks supplied content/template; `live` writes new local files through an authorized worker. Review is Tier 0, new files Tier 1, external sharing Tier 2. Do not send private material to external converters by default, run macros or overwrite the source.

**Output:** artifact paths, build decisions, visual QA evidence and unresolved compatibility issues. **Failure:** If template or renderer is unavailable, return a draft plus `partial`; a DOCX save alone is not visual QA.
