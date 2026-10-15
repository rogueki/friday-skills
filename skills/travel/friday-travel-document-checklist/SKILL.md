---
name: friday-travel-document-checklist
description: Create a privacy-preserving travel-document checklist for adults and children with official entry-rule references.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, travel, family]
---

# travel document checklist

**Use:** Use when preparing passports, tickets, insurance and child travel paperwork. Do not apply for visas or expose document numbers.

**Inputs:** Citizenship and destination as supplied, transit countries, travel dates, traveler ages at departure, document categories, official advisory access and mode.

## Procedure

1. Confirm source provenance, current capability and trip context. List identity documents, tickets, lodging confirmations, insurance, child consent or custody paperwork where relevant, medical records only if user raises them, emergency contacts and offline copies. Check entry/validity requirements with current official government or consular sources for each nationality and transit leg; distinguish requirements from suggestions. Record expiry-check results as yes/no/unknown without logging document numbers. Note documents missing or due for renewal.
2. Route any proposed external or persistent action through `friday-approval-policy` with exact target, payload and current terms.

**Mode and capability:** mock: fictional travelers; read_only: checklist; live: secure document metadata adapter may read expiry dates only with consent. Without official current sources, mark legal requirements unverified and direct user to the authority.

**Risk and approval:** Document numbers, birth dates and child details are high sensitivity. Do not upload scans or write them to ordinary logs. Applications, fees or sending documents need separate approval.

**Output and verification:** Output dated checklist, authoritative links, verification gaps and packing status. Recheck official requirements before departure and avoid claiming border admission is guaranteed. Internal `friday.skill.*` records are local lifecycle drafts, not dashboard publications.
