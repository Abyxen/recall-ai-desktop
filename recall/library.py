from __future__ import annotations

import hashlib
import json
import shutil
import uuid
from pathlib import Path

from .documents import MAX_BYTES, chunk_pages, extract
from .retrieval import Retriever


class Library:
    def __init__(self, db):
        self.db = db

    def import_file(self, path, subject='General', notebook='Notes'):
        path = Path(path)
        if not subject.strip() or not notebook.strip():
            raise ValueError("Subject and notebook cannot be empty.")
        if not path.is_file() or path.stat().st_size > MAX_BYTES:
            raise ValueError("Select a file no larger than 50 MB.")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if self.db.rows('SELECT id FROM documents WHERE digest=?', (digest,)):
            raise ValueError(f"{path.name} is already in your library (identical contents).")
        pages = extract(path, self.db.setting('ocr', False))
        chunks = chunk_pages(pages)
        retrieval = Retriever(self.db)
        vectors = []
        for offset in range(0, len(chunks), 32):
            vectors.extend(retrieval.embed([text for _, text in chunks[offset:offset + 32]]))
        root = Path(self.db.setting('library_dir', str(self.db.home / 'library')))
        root.mkdir(parents=True, exist_ok=True)
        destination = root / (uuid.uuid4().hex + path.suffix.lower())
        shutil.copy2(path, destination)
        try:
            with self.db.connect() as con:
                doc_id = con.execute('INSERT INTO documents(name,digest,subject,notebook,path,pages) VALUES(?,?,?,?,?,?)',
                                     (path.name, digest, subject.strip()[:100], notebook.strip()[:100], str(destination), len(pages))).lastrowid
                con.executemany('INSERT INTO chunks(document_id,page,text,vector,embedding) VALUES(?,?,?,?,?)',
                                [(doc_id, page, text, json.dumps(vector), retrieval.fingerprint) for (page, text), vector in zip(chunks, vectors)])
            return doc_id
        except Exception:
            destination.unlink(missing_ok=True)
            raise

    def reindex(self, doc_id):
        rows = self.db.rows('SELECT * FROM documents WHERE id=?', (doc_id,))
        if not rows:
            raise ValueError('Document no longer exists.')
        pages = extract(Path(rows[0]['path']), self.db.setting('ocr', False))
        chunks = chunk_pages(pages)
        retriever = Retriever(self.db)
        vectors = []
        for offset in range(0, len(chunks), 32):
            vectors.extend(retriever.embed([text for _, text in chunks[offset:offset + 32]]))
        with self.db.connect() as con:
            con.execute('DELETE FROM chunks WHERE document_id=?', (doc_id,))
            con.executemany('INSERT INTO chunks(document_id,page,text,vector,embedding) VALUES(?,?,?,?,?)',
                            [(doc_id, page, text, json.dumps(vector), retriever.fingerprint) for (page, text), vector in zip(chunks, vectors)])
            con.execute('UPDATE documents SET pages=? WHERE id=?', (len(pages), doc_id))

    def remove(self, doc_id):
        # Retain the managed copy and all user originals; removal only changes the database.
        self.db.execute('DELETE FROM documents WHERE id=?', (doc_id,))

    def organize(self, doc_id, subject, notebook):
        if not subject.strip() or not notebook.strip():
            raise ValueError('Subject and notebook cannot be empty.')
        self.db.execute('UPDATE documents SET subject=?, notebook=? WHERE id=?', (subject.strip()[:100], notebook.strip()[:100], doc_id))
