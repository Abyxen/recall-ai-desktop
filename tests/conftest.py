import os
import pytest
from recall.db import Database
from recall.library import Library

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')


@pytest.fixture
def db(tmp_path):
    return Database(tmp_path / 'data')


@pytest.fixture
def material(db, tmp_path):
    path = tmp_path / 'Biology.txt'
    path.write_text('Photosynthesis converts light energy into chemical energy in chloroplasts. Chlorophyll absorbs sunlight. Plants use carbon dioxide and water to produce glucose and oxygen. Mitochondria release energy through cellular respiration.', encoding='utf-8')
    doc_id = Library(db).import_file(path, 'Biology', 'Plants')
    source = db.rows('SELECT * FROM chunks WHERE document_id=?', (doc_id,))[0]
    return dict(db=db, doc_id=doc_id, source=source, path=path)


@pytest.fixture
def item(material):
    return dict(question='What does chlorophyll absorb?', answer='sunlight', topic='Photosynthesis', difficulty='medium',
                source_id=material['source']['id'], quote='Chlorophyll absorbs sunlight.', type='mcq',
                options=['sunlight', 'oxygen', 'glucose', 'soil'], key_points=[], explanation='Chlorophyll absorbs sunlight in photosynthesis.')
