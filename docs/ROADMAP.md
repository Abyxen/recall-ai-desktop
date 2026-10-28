# Roadmap and limits

## Implemented

Seven-page native desktop UI; library organization/imports/extraction/previews; persistent lexical and optional semantic vector retrieval; scoped tutor/history/citations/excerpts; validated card and quiz generation; manual/editable cards/decks; SM-2 variant reviews; quiz sessions/timers/scoring/corrections/attempts; real dashboard/activity/weak topics; configurable model endpoints; offline model-failure states; Windows setup/launch/build scripts; automated and live smoke tests; public source publication.

## Highest-value follow-ups

- Validate the portable build and one-time setup on a second clean Windows 11 laptop.
- Install and exercise optional OCR with representative scanned PDFs/images, language packs and OCR quality feedback.
- Add human score overrides and optional model-assisted rubric grading; phrase-based free-text scores remain provisional.
- Broaden factual-quality and citation-entailment evaluations. Present source evidence; do not promise hallucination-free answers.
- Add explicit per-document processing/error records, cancellation, embedding migration progress and a backup/relocation wizard. Imports currently show batch activity and per-file final errors; only successful documents enter the library.
- Add context selection across long notebooks, sentence-aware chunking, vector search acceleration and a reranker after personal-library benchmarks.
- Test an actual second OpenAI-compatible server and more embedding models; the protocol currently has local mocked coverage.
- Add light theme, accessibility/screen-reader testing, reliable streaming, signed installer and update distribution.
- Enable the included Windows CI template when workflow-scoped credentials are available.

## Deliberate current limits

No OCR tooling or AI weights bundled. No automatic downloads, account system, cloud sync or paid dependency. Calculations use numeric answer matching; units and generated derivations require review. DOCX citations are sections, not rendered pages. Local storage is unencrypted. Whole-library generation uses bounded early evidence; scope/topic selection is recommended. Exact vector search is designed for modest personal libraries. Managed copies are retained on removal and can consume disk until manually archived.
