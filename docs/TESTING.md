# Testing and verified results

Environment: Windows 11 x64; Python 3.11.17; PySide6 6.10.1; SQLite from Python; installed dependencies pinned in `requirements-lock.txt`. Results are actual executions on the developer laptop, 2026-10-28. No clean second-machine verification is claimed.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Latest suite: **47 passed**, approximately 6 seconds. Tests use temporary data and mock model responses; they require no internet connection or model weights. Qt uses its offscreen plugin. Screenshots use isolated synthetic demo data; they were visually inspected for legibility and layout. No manual human interaction testing is claimed. `pip check` also reported no broken requirements.

Coverage includes:

- Real PDF, DOCX, PPTX and UTF-16 Markdown extraction; form-feed sections; empty, corrupt, unsupported and encrypted input rejection; missing-OCR behavior.
- Source-preserving chunking, source mapping to section 2, stable normalized lexical embeddings, scoped retrieval, mismatch detection and preserving the old index after failed re-indexing.
- SQLite transactions, duplicate import detection, retained originals, re-indexing, removal, restart persistence and source snapshots.
- Structured generation, retries, invalid count/difficulty/types/options/citation/quote rejection, topic/passage selection, card creation/deduplication/editing and scheduling intervals/ratings.
- Objective scoring, bounded numeric comparison including invalid/NaN inputs, provisional phrase-rubric scores, saved quiz attempts and weak-topic aggregates.
- Missing model server, insufficient evidence, invalid tutor citations, history scope, external endpoint consent and blocked redirects.
- Local mock HTTP server testing actual Ollama and OpenAI-compatible request/response paths, non-streaming options, embeddings normalization and malformed response handling.
- Automated Qt navigation through seven pages, library preview, answer flip, due-card review, quiz submission, saved attempt and reopened dashboard state.
- Background UI import and unavailable-model evidence display; timer expiration automatically submits and saves a quiz attempt.
- Offline packaging workflow: TXT import/retrieval, saved card/review/quiz/results/reload plus real DOCX/PPTX/PDF parsing using temporary synthetic material.

## Opt-in actual model integration

```powershell
.\.venv\Scripts\python.exe tools\live_smoke.py --model axom:latest
.\.venv\Scripts\python.exe tools\live_smoke.py --model axom:latest --embedding-model qwen3-embedding:0.6b
```

**Both passed.** Ollama returned a tutor answer citing `[1]`, two cards with source-matching quotes, and two validated quiz questions. Correct-answer submission scored 2/2; card review and attempt persistence survived database reload. Semantic embedding generation, persistent vector storage and query retrieval used the actual downloaded embedding model. The script asserts the installed model exists; substitute your installed chat model. These are synthetic smoke tests, not broad model-quality or factual-grounding evaluations.

An initial run completed its workflow assertions but failed to print its final line due to Windows console encoding. UTF-8 output was added; the lexical and semantic scripts were rerun to successful exit.

## Setup and packaged checks

`powershell.exe -NoProfile -ExecutionPolicy Bypass -File setup.ps1` was executed successfully after fixing runtime discovery and PowerShell 5.1 argument quoting. It repaired a uv-created environment without pip, installed/verified the pinned dependencies and exited successfully. This is an existing-environment verification; a fresh network install on a second laptop remains untested.

Build with `powershell -NoProfile -ExecutionPolicy Bypass -File build.ps1`. The script runs pytest first and packages via PyInstaller. **Final build succeeded.** `dist\RecallAI\RecallAI.exe --smoke-test` ran on the native Windows platform with an isolated data directory, exited **0**, and returned `{"launched": true, "pages": 7, "offline_workflow": true}`. The source `run.bat --smoke-test` returned the same result.

An initial packaged launch failed because build-time PATH contained a helper tool's incompatible ICU DLL. The build script now limits PATH to the environment and Windows system directories, restores it afterwards, and uses a clean PyInstaller build. The corrected executable passed its launch and offline core-workflow checks. Its inference behavior is verified via the separate source live tests, not a live-inference packaged UI test.

To test a packaged copy with isolated data:

```powershell
$env:RECALL_DATA_DIR = Join-Path $PWD 'work\packaged-smoke'
$p = Start-Process .\dist\RecallAI\RecallAI.exe -ArgumentList '--smoke-test' -PassThru -WindowStyle Hidden
$p.WaitForExit()
Get-Content (Join-Path $env:RECALL_DATA_DIR 'smoke-result.json')
Remove-Item Env:RECALL_DATA_DIR
```

`--smoke-test` renders all pages and runs the offline dependency/workflow test in a temporary directory, writes a JSON result in the isolated data directory, then exits. Inference remains covered separately by the source live script.

## Not verified

Optional Tesseract/PyMuPDF OCR, a second real OpenAI-compatible server, offline networking physically disconnected, a clean second Windows machine, code signing, large-library performance and broad pedagogical quality. Local model APIs are loopback and no paid endpoint is required. GitHub Actions is not active because current credentials lack workflow scope; `docs/ci/windows-tests.yml` is only a template.
