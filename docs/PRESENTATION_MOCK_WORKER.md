# Presentation mock worker

`run_scenario("powerpoint")` builds a new synthetic three-slide PPTX under the ignored `artifacts/presentation-mock-*` path. `python-pptx==1.0.2` writes the file; the adapter reopens it, checks its ZIP entries and parses required XML. The content is fixed test text and makes no factual claim about the live F.R.I.D.A.Y. project.

When a local LibreOffice `libreoffice` or `soffice` executable is available, the adapter calls its headless PDF conversion with an isolated profile in that artifact directory. PyMuPDF then rasterizes all pages to PNG, checks page count, size, extractable text and basic pixel variation. The scenario reports `completed` only when these steps succeed. A missing renderer, a failed conversion or a missing rasterizer leaves it `partial`, with the reason in the result. No renderer is installed by the adapter. The Windows Apache OpenOffice 4.1.16 installation detected during development did not produce a PDF via this CLI, so it is excluded from automatic renderer selection.

This smoke check is not a human visual signoff or native Microsoft PowerPoint animation test. It does not connect to a Windows Office Worker, use an approved brand template, research live claims, or publish a deck. The deck, PDF and PNGs are local ignored artifacts; the skills package commits only the generator and tests.

Install local Python dependencies with `python -m pip install -e ".[presentation]"`.

[GitHub Actions run 38767630787](https://github.com/rogueki/friday-skills/actions/runs/38767630787) passed Windows and Ubuntu. The Ubuntu test required real LibreOffice rendering of all three slides; Windows exercised the honest `partial` path.
