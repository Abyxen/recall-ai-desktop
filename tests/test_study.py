import copy
import json
from datetime import date
import pytest
from recall.db import Database
from recall.metrics import dashboard
from recall.provider import ModelError
from recall.study import Generator, edit_card, review_card, save_cards, save_quiz, schedule, score_question, submit_quiz


class Fake:
    def __init__(self, *values):
        self.values = list(values)
        self.calls = 0

    def chat(self, messages, structured=False):
        self.calls += 1
        return self.values[min(self.calls - 1, len(self.values) - 1)]


def test_end_to_end_restart(material, item):
    db = material['db']
    fake = Fake(json.dumps({'items': [item]}))
    cards = Generator(db, fake).generate('cards', {'document_id': material['doc_id']}, count=1)
    assert save_cards(db, cards, 'Biology') == 1
    assert save_cards(db, cards, 'Biology') == 0
    card_id = db.rows('SELECT * FROM cards')[0]['id']
    edit_card(db, card_id, 'Which light does chlorophyll absorb?', 'Sunlight')
    review_card(db, card_id, 4)
    items = Generator(db, fake).generate('quiz', count=1, question_types=['mcq'])
    quiz = save_quiz(db, 'Plants', items)
    result = submit_quiz(db, quiz, ['oxygen'])
    assert result['score'] == 0 and result['feedback'][0]['quote'] == item['quote']
    assert submit_quiz(db, quiz, ['sunlight'])['score'] == 1
    reopened = Database(db.home)
    assert reopened.rows('SELECT * FROM cards')[0]['answer'] == 'Sunlight'
    assert len(reopened.rows('SELECT * FROM attempts')) == 2
    assert len(reopened.rows('SELECT * FROM reviews')) == 1
    stats = dashboard(reopened)
    assert stats['documents'] == 1 and stats['notebooks'] == 1 and stats['due'] == 0
    assert stats['weak_topics'][0][0] == 'Photosynthesis'


def test_structured_retry(material, item):
    fake = Fake('bad json', json.dumps({'items': [item]}))
    assert Generator(material['db'], fake).generate('cards', count=1)
    assert fake.calls == 2
    fake = Fake('{"items": []}')
    with pytest.raises(ModelError, match='3 attempts'):
        Generator(material['db'], fake).generate('cards', count=1)
    assert fake.calls == 3


@pytest.mark.parametrize('change', [dict(source_id=999), dict(quote='A fabricated source quotation.'), dict(question='Why?'), dict(difficulty='extreme'), dict(options=['sunlight'] * 4), dict(answer='not an option'), dict(type='invalid')])
def test_invalid_generation(material, item, change):
    item.update(change)
    fake = Fake(json.dumps({'items': [item]}))
    with pytest.raises(ModelError):
        Generator(material['db'], fake).generate('quiz', count=1, question_types=['mcq'])


@pytest.mark.parametrize('count', [0, 21, True, -1])
def test_count_validation(material, count):
    with pytest.raises(ValueError):
        Generator(material['db'], Fake('')).generate('cards', count=count)


def test_topic_and_passage(material, item):
    generator = Generator(material['db'], Fake(json.dumps({'items': [item]})))
    assert generator.material(topic='chlorophyll', passage=item['quote'])
    with pytest.raises(ValueError, match='No matching'):
        generator.material(passage='This sentence is absent from the document.')


def test_schedule():
    card = dict(repetitions=0, interval=0, ease=2.5)
    first = schedule(card, 4, date(2026, 1, 1))
    assert first['interval'] == 1 and first['due'] == '2026-01-02'
    second = schedule(first, 4, date(2026, 1, 2))
    assert second['interval'] == 6 and second['repetitions'] == 2
    third = schedule(second, 5, date(2026, 1, 8))
    assert third['interval'] > 6
    again = schedule(third, 1, date(2026, 1, 9))
    assert again['interval'] == 1 and again['repetitions'] == 0 and again['ease'] >= 1.3
    with pytest.raises(ValueError):
        schedule(card, 7)


@pytest.mark.parametrize('kind,response,answer,expected', [('mcq', 'Sunlight', 'sunlight', 1), ('true_false', 'false', 'true', 0), ('calculation', '10.005', '10', 1), ('calculation', '11', '10', 0), ('calculation', 'NaN', '10', 0), ('calculation', '', '10', 0)])
def test_scoring(item, kind, response, answer, expected):
    item.update(type=kind, answer=answer, source='Biology.txt')
    assert score_question(item, response)['score'] == expected


def test_provisional_rubric(item):
    item.update(type='explanation', key_points=['light energy', 'chemical energy'], source='Biology.txt')
    result = score_question(item, 'It uses light energy.')
    assert result['score'] == .5 and result['provisional']


def test_transaction_and_input_validation(db):
    with pytest.raises(ValueError):
        with db.connect() as con:
            con.execute('INSERT INTO settings VALUES(?,?)', ('rollback', '1'))
            raise ValueError()
    assert db.setting('rollback') is None
    with pytest.raises(ValueError):
        edit_card(db, 99, 'tiny', '')
    with pytest.raises(ValueError):
        save_cards(db, [], '')
    with pytest.raises(ValueError):
        review_card(db, 99, 4)
    with pytest.raises(ValueError):
        submit_quiz(db, 99, [])
