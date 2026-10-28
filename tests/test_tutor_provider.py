import json
import pytest
from recall.provider import ModelError, Provider
from recall.retrieval import Retriever, lexical_vector, scope_sql
from recall.tutor import Tutor


class Fake:
    def __init__(self, answer):
        self.answer = answer
        self.messages = []

    def chat(self, messages, **kwargs):
        self.messages = messages
        if isinstance(self.answer, Exception):
            raise self.answer
        return self.answer


def test_tutor_citations_and_scope(material):
    db = material['db']
    provider = Fake('Chlorophyll absorbs sunlight [1].')
    result = Tutor(db, provider).ask('What does chlorophyll absorb?', {'subject': 'Biology'})
    assert result['evidence'][0]['document_id'] == material['doc_id']
    assert '[1]' in result['answer'] and result['status'].startswith('model answer')
    assert db.rows('SELECT * FROM conversations')
    Tutor(db, provider).ask('Explain it again', {'subject': 'Physics'})
    assert len(db.rows('SELECT * FROM conversations')) == 2
    result = Tutor(db, Fake('Made up [900]')).ask('chlorophyll?')
    assert result['status'].startswith('evidence only')
    result = Tutor(db, Fake('Uncited answer')).ask('chlorophyll?')
    assert 'did not provide inline citations' in result['answer']


def test_missing_model(material):
    result = Tutor(material['db'], Fake(ModelError('Offline'))).ask('photosynthesis?')
    assert result['evidence'] and 'Offline' in result['answer']
    assert 'not an AI explanation' in result['answer']


def test_insufficient_evidence(db):
    assert Tutor(db).ask('What is photosynthesis?')['status'] == 'insufficient evidence'
    with pytest.raises(ValueError):
        Tutor(db).ask('')


def test_external_endpoint_consent(db):
    db.configure(endpoint='https://example.org/v1')
    with pytest.raises(ModelError, match='blocked'):
        Provider(db)
    db.configure(allow_external=True)
    assert Provider(db).external
    db.configure(endpoint='file:///tmp/data')
    with pytest.raises(ModelError):
        Provider(db)
    db.configure(endpoint='http://name:secret@localhost:1234')
    with pytest.raises(ModelError):
        Provider(db)


def test_refused_server(db):
    db.configure(endpoint='http://127.0.0.1:1', timeout=1)
    with pytest.raises(ModelError, match='unavailable'):
        Provider(db).models()


def test_vectors_and_embedding_change(material):
    assert lexical_vector('photosynthesis') == lexical_vector('photosynthesis')
    assert sum(v * v for v in lexical_vector('photosynthesis sunlight')) == pytest.approx(1)
    db = material['db']
    db.configure(embedding_model='new-model')
    with pytest.raises(ValueError, match='Re-index'):
        Retriever(db).search('sunlight')
    with pytest.raises(ValueError):
        scope_sql({'malicious': 'x'})
