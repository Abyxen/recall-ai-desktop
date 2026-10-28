import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import pytest
from recall.provider import ModelError, Provider
from recall.retrieval import Retriever


@pytest.fixture
def server():
    requests = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            self.reply()

        def do_POST(self):
            self.reply()

        def reply(self):
            size = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(size)) if size else None
            requests.append((self.path, data))
            if self.path == '/redirect':
                self.send_response(302)
                self.send_header('Location', '/leaked')
                self.end_headers()
                return
            payloads = {
                '/api/tags': {'models': [{'name': 'test'}]},
                '/v1/models': {'data': [{'id': 'test'}]},
                '/api/chat': {'message': {'content': 'A cited answer [1]'}},
                '/v1/chat/completions': {'choices': [{'message': {'content': 'OpenAI-compatible local answer'}}]},
                '/api/embed': {'embeddings': [[.1, .2, .3]]},
                '/v1/embeddings': {'data': [{'index': 0, 'embedding': [.1, .2, .3]}]},
                '/empty': {},
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(payloads.get(self.path, {})).encode())
    http = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{http.server_port}', requests
    http.shutdown()
    http.server_close()
    thread.join()


@pytest.mark.parametrize('kind', ['ollama', 'openai'])
def test_wire_protocol(db, server, kind):
    base, requests = server
    db.configure(provider=kind, endpoint=base + ('/v1' if kind == 'openai' else ''), model='test', embedding_model='test-embed')
    provider = Provider(db)
    assert provider.models() == ['test']
    assert provider.chat([{'role': 'user', 'content': 'Question'}], structured=True)
    assert provider.embed(['test']) == [[.1, .2, .3]]
    assert requests[1][1]['stream'] is False
    vector = Retriever(db).embed(['test'])[0]
    assert sum(v * v for v in vector) == pytest.approx(1)


def test_no_redirects(db, server):
    base, requests = server
    db.configure(endpoint=base)
    with pytest.raises(ModelError):
        Provider(db).request('/redirect', {'private': 'document text'})
    assert len(requests) == 1 and requests[0][0] == '/redirect'


def test_invalid_vectors(db, monkeypatch):
    db.configure(embedding_model='test')
    for vectors in [[], [[float('nan')]], [[1, 2], [3]], [['bad']]]:
        monkeypatch.setattr(Provider, 'embed', lambda self, texts, values=vectors: values)
        with pytest.raises((ValueError, TypeError)):
            Retriever(db).embed(['test'])


@pytest.mark.parametrize('kind', ['ollama', 'openai'])
def test_malformed_server_responses(db, monkeypatch, kind):
    db.configure(provider=kind, model='test')
    provider = Provider(db)
    for result in [{}, {'message': None}, {'choices': [None]}, {'models': [None]}, {'data': None}]:
        monkeypatch.setattr(provider, 'request', lambda *args, payload=result, **kwargs: payload)
        with pytest.raises(ModelError):
            provider.chat([{'role': 'user', 'content': 'test'}])
        with pytest.raises(ModelError):
            provider.models()
        with pytest.raises(ModelError):
            provider.embed(['test'])
