# Model setup

Verified locally: Ollama with existing `axom:latest` (4.2B Q4_K_M) and, following explicit consent, `qwen3-embedding:0.6b` (639 MB). Both live lexical and semantic end-to-end workflows passed. Recall delegates GPU support and model loading to Ollama; it does not assume a CUDA/PyTorch backend in its Python environment.

1. Install Ollama from [the official site](https://ollama.com), start it, and run `ollama list`.
2. Use an existing instruct model when possible. In Settings choose provider `ollama`, endpoint `http://localhost:11434`, test/list models, choose one and Save.
3. If you need a model, [qwen3:4b](https://ollama.com/library/qwen3:4b) is a practical 2.5 GB starting point for a 32 GB laptop. This sizing recommendation does not establish model quality or exact VRAM usage on your hardware. Install manually with `ollama pull qwen3:4b`. This tag was verified in the official registry; the live tests used the already-installed custom Axom model instead.
4. Optional semantic retrieval: `ollama pull qwen3-embedding:0.6b`. Set that name in Embedding model, save, then re-index existing documents. The [official embedding model page](https://ollama.com/library/qwen3-embedding:0.6b) and [API reference](https://docs.ollama.com/api/embed) describe the local `/api/embed` endpoint. Recall stores the resulting vectors locally.
5. Blank embedding model selects the lexical fallback. It works without an embedding server and matches exact words better than paraphrases. Switching either direction requires re-indexing.

Recall never automatically downloads weights. First model load can take longer; adjust timeout in Settings (10–600 seconds per request). Structured generation may make up to three requests. If CPU/GPU memory is constrained, close other model applications, shorten the evidence scope and use fewer generated items. Check `ollama ps` to see active models and device allocation; no GPU benchmark is claimed by this project.

## OpenAI-compatible local inference

Select provider `openai`, use the server's base URL including `/v1` (for example `http://localhost:1234/v1`), and test/list models. Endpoint compatibility is covered by a local mock HTTP server; no second real inference server was installed for verification. Servers must support the chat, models and optionally embeddings routes. Some servers do not support `response_format: json_object`; choose a compatible server/model if structured generation fails. Use `RECALL_API_KEY` only if your chosen server requires a key. Do not put keys in endpoint URLs or source files.

Only `localhost`, `127.0.0.1` and `::1` are classified as local. Any other host, including a LAN IP, requires explicit external-data consent. With that enabled, relevant document text, embedding input, questions and conversation context go to the configured server. Use HTTPS for non-local connections. Server availability checks list models; a successful list does not prove that every model supports chat or embeddings.

## Optional OCR

Install a trusted Tesseract distribution and add its executable directory to PATH. Enable OCR in Settings and restart after PATH changes. Images require it. Scanned PDFs also need `pip install PyMuPDF` in the Recall environment (optional dependency; consider its licensing terms). Re-index to process previously imported PDFs. OCR is not available in the verified developer environment and is not bundled in the executable. Text PDFs and Office/text formats do not depend on OCR.
