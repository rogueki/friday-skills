# Offline research, source verification and decision brief (§22)

`adapters/research_e2e_mock.py` composes three existing F.R.I.D.A.Y. procedures against four pinned **synthetic** HTML pages. It is an offline test path for `friday-deep-research`, `friday-source-verification` and `friday-decision-brief`; it is not a Hermes tool or a claim that these skills executed inside Hermes.

Run:

```powershell
python -m unittest discover -s tests -p test_research_e2e_mock.py -v
```

The manifest in `fixtures/research/case.json` names a question, common 12-month comparison period, three options, publisher claims, publication and retrieval times, independence groups, HTML locators and pinned SHA-256 values. The adapter checks the current bytes before extracting the pages with `adapters/web_extraction.py` and an injected local transport. Extracted rows form a claim ledger with source ID, passage locator, date, source hash, value, scope and excluded evidence. A source hash proves only that bytes match this fixture; it does not prove authorship, publication date, independence or real-world truth.

The two independent primary fixtures disagree about the local annual cost (120 versus 150 EUR). A 2024 syndicated copy of a hosted quote supplies a different period and shares the vendor's independence group; it does not corroborate the current 90 EUR hosted quote. The current hosted price has only one synthetic vendor source. Status-quo cost, hosted data-control terms and the decision owner's priorities are absent. The brief compares all three options and names the smallest reversible evidence-gathering step; it withholds a winner and any authorization for purchase or contact.

Negative variants exercise an instruction embedded in source text, altered bytes after capture, a missing or stale primary source, and incompatible comparison periods. A failed variant produces no decision brief. Every variant reports zero network/provider calls and external effects by construction; the parser transport returns fixture bytes and cannot open a connection. The test does not validate live research, a search provider, source authenticity, a scheduler, Hermes routing or individual Hermes skill runtime behavior. A live source would need a separately authorized host-controlled transport and fresh provenance verification.
