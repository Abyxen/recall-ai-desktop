from __future__ import annotations

import hashlib
import json
import re

import numpy as np

from .provider import Provider

STOP = set('a an the is are was were be been to of in on for and or it this that what how why explain describe please from with as by at do does tell me about'.split())


def tokens(text):
    return [t for t in re.findall(r"[^\W_]+", text.casefold(), re.UNICODE) if t not in STOP]


def lexical_vector(text, dimensions=768):
    words = tokens(text)
    features = words + [a + ':' + b for a, b in zip(words, words[1:])]
    vector = np.zeros(dimensions, dtype=float)
    for word in features:
        index = int.from_bytes(hashlib.blake2b(word.encode(), digest_size=4).digest(), 'little') % dimensions
        vector[index] += 1
    norm = np.linalg.norm(vector)
    return (vector / norm if norm else vector).tolist()


class Retriever:
    def __init__(self, db):
        self.db = db

    @property
    def fingerprint(self):
        model = self.db.setting('embedding_model', '').strip()
        return 'lexical-hash-v1' if not model else '|'.join((self.db.setting('provider', 'ollama'), self.db.setting('endpoint', 'http://localhost:11434'), model))

    def embed(self, texts):
        if self.fingerprint == 'lexical-hash-v1':
            return [lexical_vector(t) for t in texts]
        vectors = Provider(self.db).embed(texts)
        if len(vectors) != len(texts) or not vectors:
            raise ValueError("Embedding server returned the wrong number of vectors.")
        arrays = [np.asarray(v, dtype=float) for v in vectors]
        if any(v.ndim != 1 or not len(v) or not np.all(np.isfinite(v)) for v in arrays) or len({len(v) for v in arrays}) != 1:
            raise ValueError("Embedding server returned invalid vectors.")
        return [(v / (np.linalg.norm(v) or 1)).tolist() for v in arrays]

    def search(self, question, scope=None, limit=5):
        if not question.strip():
            raise ValueError("Enter a question first.")
        where, params = scope_sql(scope)
        rows = self.db.rows('SELECT c.*,d.name,d.subject,d.notebook FROM chunks c JOIN documents d ON d.id=c.document_id ' + where, params)
        if not rows:
            return []
        matching = [row for row in rows if row['embedding'] == self.fingerprint]
        if not matching:
            raise ValueError("Embedding configuration changed. Re-index the selected documents in My Library.")
        query = np.asarray(self.embed([question])[0])
        result = []
        qwords = set(tokens(question))
        for row in matching:
            vector = np.asarray(json.loads(row['vector']))
            if vector.shape != query.shape:
                continue
            similarity = float(np.dot(query, vector))
            overlap = len(qwords & set(tokens(row['text'])))
            if similarity > 0.12 and (self.fingerprint != 'lexical-hash-v1' or overlap):
                row['score'] = similarity
                row.pop('vector')
                result.append(row)
        result.sort(key=lambda row: row['score'], reverse=True)
        return result[:limit]


def scope_sql(scope=None):
    scope = scope or {}
    allowed = {'document_id': 'd.id', 'subject': 'd.subject', 'notebook': 'd.notebook'}
    conditions, params = [], []
    for key, value in scope.items():
        if key not in allowed:
            raise ValueError("Invalid library scope.")
        conditions.append(allowed[key] + '=?')
        params.append(value)
    return ('WHERE ' + ' AND '.join(conditions) if conditions else ''), params


def source_label(row):
    suffix = row['name'].lower().rsplit('.', 1)[-1]
    unit = 'slide' if suffix == 'pptx' else 'section' if suffix in {'docx', 'txt', 'md'} else 'page'
    return f"{row['name']} · {unit} {row['page']}"
