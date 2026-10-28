"""Opt-in integration test against an already installed local Ollama model. No downloads."""
import argparse
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from recall.db import Database
from recall.library import Library
from recall.provider import Provider
from recall.retrieval import Retriever
from recall.study import Generator, review_card, save_cards, save_quiz, submit_quiz
from recall.tutor import Tutor


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default='axom:latest')
    parser.add_argument('--embedding-model', default='')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        db = Database(root / 'data')
        db.configure(model=args.model, embedding_model=args.embedding_model, timeout=180)
        assert args.model in Provider(db).models(), 'Requested chat model is not installed.'
        path = root / 'Synthetic biology lesson.txt'
        path.write_text('Photosynthesis converts light energy into chemical energy in chloroplasts. Chlorophyll absorbs sunlight. Plants use carbon dioxide and water to produce glucose and oxygen. Cellular respiration in mitochondria releases energy from glucose. The nucleus contains genetic material called DNA.', encoding='utf-8')
        doc_id = Library(db).import_file(path, 'Biology', 'Synthetic test')
        assert Retriever(db).search('How do plants convert sunlight into stored energy?')
        result = Tutor(db).ask('What does chlorophyll absorb?', {'document_id': doc_id})
        assert result['status'].startswith('model answer'), result
        assert '[1]' in result['answer'], result
        print('LIVE TUTOR:', result['answer'], flush=True)
        cards = Generator(db).generate('cards', {'document_id': doc_id}, count=2)
        assert save_cards(db, cards, 'Live smoke') == 2
        review_card(db, db.rows('SELECT id FROM cards')[0]['id'], 4)
        print('LIVE FLASHCARDS:', json.dumps(cards, ensure_ascii=False), flush=True)
        quiz = Generator(db).generate('quiz', {'document_id': doc_id}, count=2, question_types=['mcq', 'true_false'])
        quiz_id = save_quiz(db, 'Live smoke quiz', quiz)
        assert submit_quiz(db, quiz_id, [item['answer'] for item in quiz])['score'] == 2
        reopened = Database(root / 'data')
        assert len(reopened.rows('SELECT * FROM cards')) == 2
        assert len(reopened.rows('SELECT * FROM attempts')) == 1
        print('LIVE QUIZ:', json.dumps(quiz, ensure_ascii=False), flush=True)
        print('PASS: live import > retrieval > cited tutor > cards > review > quiz > score > reload', flush=True)


if __name__ == '__main__':
    main()
