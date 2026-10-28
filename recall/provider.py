from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from urllib.parse import urlparse


class ModelError(RuntimeError):
    pass


class Provider:
    def __init__(self, db):
        self.db = db
        self.endpoint = db.setting("endpoint", "http://localhost:11434").rstrip('/')
        self.kind = db.setting("provider", "ollama")
        self.model = db.setting("model", "")
        parsed = urlparse(self.endpoint)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            raise ModelError("Use a valid HTTP(S) endpoint without embedded credentials.")
        self.external = parsed.hostname.lower() not in {"localhost", "127.0.0.1", "::1"}
        if self.external and not db.setting("allow_external", False):
            raise ModelError("External endpoint blocked. Enable the explicit external-data consent in Settings first.")

    def request(self, path, payload=None, timeout=None):
        headers = {"Content-Type": "application/json"}
        if os.environ.get("RECALL_API_KEY"):
            headers["Authorization"] = "Bearer " + os.environ["RECALL_API_KEY"]
        req = urllib.request.Request(self.endpoint + path,
                                     data=json.dumps(payload).encode() if payload is not None else None,
                                     headers=headers)
        # Do not follow redirects that might disclose local document content.
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None
        try:
            with urllib.request.build_opener(NoRedirect).open(req, timeout=timeout or self.db.setting("timeout", 120)) as response:
                result = json.loads(response.read(8 * 1024 * 1024))
                if not isinstance(result, dict):
                    raise ValueError('Expected a JSON object from the model server.')
                return result
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            raise ModelError(f"Model server unavailable or returned invalid data ({exc}). Start Ollama or check Settings → Test connection.") from exc

    def models(self):
        result = self.request('/api/tags' if self.kind == 'ollama' else '/models', timeout=8)
        try:
            names = [m['name'] for m in result['models']] if self.kind == 'ollama' else [m['id'] for m in result['data']]
            if any(not isinstance(name, str) for name in names):
                raise ValueError()
            return names
        except (KeyError, TypeError, ValueError):
            raise ModelError('The model list response has an unexpected format. Check provider and base URL.')

    def chat(self, messages, structured=False):
        if not self.model.strip():
            raise ModelError("Choose an installed model in Settings.")
        temperature = self.db.setting('temperature', 0.2)
        if self.kind == 'ollama':
            payload = dict(model=self.model, messages=messages, stream=False, think=False,
                           options=dict(temperature=temperature, num_predict=3072, num_ctx=8192))
            if structured:
                payload['format'] = 'json'
            result = self.request('/api/chat', payload)
            message = result.get('message')
        else:
            payload = dict(model=self.model, messages=messages, temperature=temperature, max_tokens=3072, stream=False)
            if structured:
                payload['response_format'] = {'type': 'json_object'}
            result = self.request('/chat/completions', payload)
            choices = result.get('choices')
            message = choices[0].get('message') if isinstance(choices, list) and choices and isinstance(choices[0], dict) else None
        if not isinstance(message, dict):
            raise ModelError('Unexpected chat response format. Check that the provider and base URL match your server.')
        content = message.get('content', '')
        if not isinstance(content, str) or not content.strip():
            raise ModelError("The model returned an empty answer. Try a different model or a shorter request.")
        return content.strip()

    def embed(self, texts):
        model = self.db.setting('embedding_model', '').strip()
        try:
            if self.kind == 'ollama':
                return self.request('/api/embed', {'model': model, 'input': texts})['embeddings']
            return [d['embedding'] for d in sorted(self.request('/embeddings', {'model': model, 'input': texts})['data'], key=lambda d: d['index'])]
        except (KeyError, TypeError):
            raise ModelError('Unexpected embeddings response. Choose an installed embedding-capable model.')
