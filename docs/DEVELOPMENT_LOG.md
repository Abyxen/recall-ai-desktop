# Development log

## Milestone 1 — document foundation

Implemented SQLite storage, copied-file imports, PDF/DOCX/PPTX/TXT/Markdown parsers, optional OCR, chunking with source positions, persistent lexical vector retrieval, configurable model provider and minimal runnable desktop shell. Python 3.11.17 and pinned dependencies installed. No model downloads.

Validation: 2 pytest tests passed; offscreen Qt desktop shell launched and closed successfully. Commit `104e60f` pushed successfully to the new public repository.

## Milestone 2 — study workflow and desktop product

Implemented seven-page desktop UI; asynchronous imports/inference; library organization and previews; scoped tutor/history with source excerpts; structured generation with three validation attempts and exact-source quote checks; editable decks; SM-2 variant review scheduling; quiz sessions, timer, deterministic answer checking, provisional phrase-rubric free-text scores, saved attempts, weak topics and real activity metrics. Added Windows setup/launch/build scripts, pinned lock file and CI workflow.

Validation: 38 tests passed, including PDF/DOCX/PPTX parsing and offscreen desktop import-preview/card-review/quiz/reload workflow. Actual local `axom:latest` API returned a cited tutor answer, two valid cards and two quiz questions; lexical live workflow passed after fixing a Windows console encoding issue in the smoke script. User authorized the 639 MB `qwen3-embedding:0.6b` download; installation succeeded. Semantic live workflow is being tested. Visual QA found missing fonts in the Qt offscreen plugin; explicit system font registration added.

Known limits: generated content still requires human accuracy checks; calculation scoring verifies numeric matching only; free-text grading is provisional; OCR requires external optional programs; semantic index uses exact linear cosine search, suited to personal libraries. Packaging and final documentation follow.

