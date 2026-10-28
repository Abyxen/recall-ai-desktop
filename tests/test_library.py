import pytest
from recall.db import Database
from recall.documents import Page, chunk_pages, extract
from recall.library import Library
from recall.retrieval import Retriever, source_label


def test_import_retrieve_restart_remove(tmp_path):
    original = tmp_path / 'biology.txt'
    original.write_text('Photosynthesis converts light energy into chemical energy in chloroplasts. Chlorophyll absorbs sunlight.', encoding='utf-8')
    db = Database(tmp_path / 'data')
    doc_id = Library(db).import_file(original, 'Biology', 'Plants')
    result = Retriever(db).search('What does photosynthesis convert?')
    assert result[0]['document_id'] == doc_id
    assert result[0]['page'] == 1
    assert source_label(result[0]) == 'biology.txt · section 1'
    with pytest.raises(ValueError, match='already'):
        Library(db).import_file(original)
    db = Database(tmp_path / 'data')
    assert len(db.rows('SELECT * FROM documents')) == 1
    Library(db).reindex(doc_id)
    assert Retriever(db).search('photosynthesis', {'subject': 'Physics'}) == []
    assert Retriever(db).search('photosynthesis', {'notebook': 'Plants'})
    Library(db).remove(doc_id)
    assert not db.rows('SELECT * FROM chunks')
    assert original.exists()


def test_pages_and_validation(tmp_path):
    chunks = chunk_pages([Page(3, 'one two three four five'), Page(4, 'six seven')], size=3, overlap=1)
    assert chunks == [(3, 'one two three'), (3, 'three four five'), (4, 'six seven')]
    with pytest.raises(ValueError):
        chunk_pages([], 3, 3)
    path = tmp_path / 'bad.pdf'
    path.write_text('broken')
    with pytest.raises(ValueError, match='Cannot read'):
        extract(path)
    path = tmp_path / 'empty.txt'
    path.touch()
    with pytest.raises(ValueError, match='empty'):
        extract(path)
