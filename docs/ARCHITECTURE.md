# Architecture

Recall AI is a Python/PySide6 desktop application using a single local SQLite database. There is no hosted backend.

## Modules and flow

- `__main__.py`: application bootstrap and packaged/source launch smoke mode.
- `ui.py`: window, navigation, Dashboard, Library and Progress.
- `ui_tutor.py`, `ui_study.py`, `widgets.py`, `theme.py`: tutor/settings, card/quiz sessions, reusable controls and dark theme. Long imports and inference run via QThreadPool workers, with signals returning results to the GUI thread. Quiz timing uses a GUI QTimer. Closing is prevented while a worker is active.
- `documents.py`: format validation, parsers, optional local OCR and source-preserving chunking. PDF pages and PPTX slides are preserved; DOCX cannot expose reliable rendered page boundaries, so it is one section. Chunks are 180 words with 35-word overlap and never span source units.
- `library.py`: bounded file import → digest duplicate check → extraction → chunking → embedding → managed copy → atomic SQLite insert. Originals are untouched. Re-index creates all replacement vectors before replacing the old index in one transaction. Removal deletes the record/index but retains managed copies and study history.
- `retrieval.py`: normalized local embeddings and cosine retrieval. Default lexical feature hashing uses word/unigram and bigram counts in 768 dimensions with stable BLAKE2 hashing. Optional Ollama/OpenAI-compatible semantic embeddings are locally configurable. Vectors and provider/endpoint/model fingerprints are persisted alongside each chunk; mismatched indexes require re-indexing. Search is exact linear cosine, scoped by parameterized SQL. Lexical results additionally require actual token overlap and receive a query-coverage boost.
- `provider.py`: stdlib HTTP adapter for Ollama `/api/tags`, `/api/chat`, `/api/embed` or OpenAI-compatible `/models`, `/chat/completions`, `/embeddings`. OpenAI base URL includes `/v1`. Timeouts, finite response size, no redirects, explicit external endpoint consent and optional environment-only bearer key. No model downloads. Responses are intentionally non-streaming for reliability.
- `tutor.py`: scoped retrieval → numbered evidence prompt → model response → citation-number validation → saved conversation and evidence snapshot. No matches yields insufficient-evidence text without inference. Inference failure yields original excerpts with a clear unavailable notice. A scope gets its own three-turn context. Anaphoric follow-ups may retrieve from the last question when their own retrieval is empty.
- `study.py`: grounded JSON generation, type/count/difficulty/source/quote validation with up to three attempts, card persistence/editing, scheduling, deterministic objective/numeric checks, provisional free-text rubric scoring and attempt persistence.
- `metrics.py`: real database aggregates; no injected sample statistics. Weak topics average question-level scores from up to 100 recent attempts, including provisional free-text scores.

## SQLite schema

`documents` stores metadata, source-unit count, digest and managed-copy path. `chunks` stores page/slide/section, text, vector and embedding fingerprint. Document deletion cascades to chunks.

`cards` stores deck, question, answer, topic, difficulty, source snapshot, ease, repetitions, interval and due date. `reviews` retains rating/timestamp even if a card is deleted. A removed document clears a card's document foreign key but retains the card/source snapshot.

`quizzes` stores validated question JSON. `attempts` stores answers, question-level feedback, total score and timestamp. `conversations` stores a canonical scope key and complete evidence snapshots. `settings` stores JSON values without API keys. Foreign keys, WAL and per-operation connections allow worker reads/writes; writes are transactional. Schema version is 1; future structural changes need migrations.

## Review algorithm

SM-2 variant: Again=1, Hard=3, Good=4, Easy=5. Ease changes by `0.1 - (5-q)*(0.08+(5-q)*0.02)` with minimum 1.3. Again resets repetitions to zero and schedules tomorrow. Successful first/second reviews use 1/6 days; later reviews multiply interval by updated ease and round to whole days. Reviews always record history. Due dates use the machine's local calendar; activity timestamps are stored UTC and grouped in local time.

## Trust boundaries and limitations

Imported documents are untrusted data. They are parsed, never executed; prompts explicitly reject embedded instructions. This reduces but does not eliminate prompt-injection risk. Generated Markdown cannot load local/remote resources or open links. External endpoint use is opt-in and sends retrieved text, prompts, history and/or embedding inputs. Model-generated facts need source review even with structurally valid citations. Files and database contents are not encrypted. Parsers run in worker threads, not an OS sandbox; use trusted documents and observe resource limits.
