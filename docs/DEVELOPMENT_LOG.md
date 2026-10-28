# Development log

## Milestone 1 — document foundation

Implemented SQLite storage, copied-file imports, PDF/DOCX/PPTX/TXT/Markdown parsers, optional OCR, chunking with source positions, persistent lexical vector retrieval, configurable model provider and minimal runnable desktop shell. Python 3.11.17 and pinned dependencies installed. No model downloads.

Validation: 2 pytest tests passed; offscreen Qt desktop shell launched and closed successfully. Commit `104e60f` pushed successfully to the new public repository.

## Milestone 2 — study workflow and desktop product

Implemented seven-page desktop UI; asynchronous imports/inference; library organization and previews; scoped tutor/history with source excerpts; structured generation with three validation attempts and exact-source quote checks; editable decks; SM-2 variant review scheduling; quiz sessions, timer, deterministic answer checking, provisional phrase-rubric free-text scores, saved attempts, weak topics and real activity metrics. Added Windows setup/launch/build scripts, pinned lock file and CI workflow.

Validation: 38 tests passed, including PDF/DOCX/PPTX parsing and offscreen desktop import-preview/card-review/quiz/reload workflow. Actual local `axom:latest` API returned a cited tutor answer, two valid cards and two quiz questions; lexical live workflow passed after fixing a Windows console encoding issue in the smoke script. User authorized the 639 MB `qwen3-embedding:0.6b` download; installation succeeded. Semantic live workflow is being tested. Visual QA found missing fonts in the Qt offscreen plugin; explicit system font registration added.

Known limits: generated content still requires human accuracy checks; calculation scoring verifies numeric matching only; free-text grading is provisional; OCR requires external optional programs; semantic index uses exact linear cosine search, suited to personal libraries. Packaging and final documentation follow.


Publication note: milestone 2 commit 7f09b6e was initially rejected because GitHub OAuth credentials lack workflow scope. Moved the CI definition to docs/ci/windows-tests.yml as an opt-in template, preserving all application code and history.

The corrective commit `f1c7288` and the full milestone 2 source were subsequently pushed successfully and verified against the remote main branch.

## Milestone 3 — regression, reproducibility and portable Windows build

Final verification: **47 pytest tests passed** (about 6 seconds); `pip check` reported no broken requirements. Added real local HTTP protocol tests, malformed response errors, redirect protection, source-position and failed re-index regression, background GUI import/model failure, timed submission, and an isolated offline packaging smoke test. Cards now save deck edits atomically; selection-dependent controls disable correctly; generated Markdown cannot load resources. New installs require an explicitly selected chat model rather than assuming the developer's custom model exists.

Actual lexical and `qwen3-embedding:0.6b` semantic live workflows both passed using existing `axom:latest`: import, retrieval, source-cited tutor response, two quote-validated cards, review, two validated quiz questions, 2/2 scoring and database reload. The embedding model was downloaded only after explicit user consent. The local application data directory was configured for these installed models, with no synthetic study documents added to it.

Windows `setup.ps1` completed after fixes for third-party Python runtime discovery and PowerShell 5.1 quoting. Source `run.bat --smoke-test` passed. PyInstaller produced a portable windowed folder including dependency license metadata and documentation. Initial frozen startup failed on an incompatible ICU library from a helper-tool PATH; a clean build with a restricted build-time PATH fixed it. **Final executable exited 0** and recorded `launched=true`, `pages=7`, `offline_workflow=true`, covering rendering plus TXT retrieval/card/review/quiz/reload and DOCX/PPTX/PDF parsing. A startup error log now makes future failures inspectable.

Documentation completed: setup, usage, model/OCR configuration, architecture/schema, privacy, test results, troubleshooting, screenshots and honest follow-up roadmap. Screenshots were visually reviewed and use isolated synthetic demo data. Repository review found no private documents, databases, credentials or model weights in tracked files. Source and final portable distribution are separate; local data remains outside the repository. Final publication/hash verification is performed with this milestone commit.

Remaining limits: optional OCR and a second real OpenAI-compatible server were not exercised; fresh second-machine setup, code signing and large-library performance remain unverified. Free-text grades are provisional phrase-rubric coverage, generated mathematics is not independently verified, and source quote matching does not guarantee factual entailment. CI remains an inactive template due to OAuth workflow permission. See ROADMAP.md.
