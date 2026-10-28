"""Capture application screenshots using isolated, explicitly synthetic data."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import sys
from pathlib import Path
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from recall.db import Database
from recall.library import Library
from recall.study import save_cards, save_quiz, submit_quiz
from recall.ui import MainWindow

app = QApplication.instance() or QApplication([])
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    db = Database(root / 'data')
    path = root / 'DEMO - Photosynthesis.txt'
    path.write_text('Photosynthesis converts light energy into chemical energy in chloroplasts. Chlorophyll absorbs sunlight. Plants use carbon dioxide and water to produce glucose and oxygen.', encoding='utf-8')
    doc_id = Library(db).import_file(path, 'Biology', 'Plant systems')
    item = dict(document_id=doc_id, question='What does chlorophyll absorb?', answer='Sunlight', topic='Photosynthesis', difficulty='medium', source='DEMO - Photosynthesis.txt · section 1', quote='Chlorophyll absorbs sunlight.', type='mcq', options=['Sunlight', 'Glucose', 'Water', 'DNA'], explanation='Chlorophyll absorbs sunlight during photosynthesis.', key_points=[])
    save_cards(db, [item], 'Biology essentials')
    quiz_id = save_quiz(db, 'DEMO - Plant systems', [item])
    submit_quiz(db, quiz_id, ['Sunlight'])
    window = MainWindow(db)
    window.show()
    destination = Path(__file__).resolve().parents[1] / 'docs' / 'screenshots'
    destination.mkdir(exist_ok=True)
    for index, name in [(0, 'dashboard'), (1, 'library'), (3, 'flashcards'), (5, 'progress')]:
        window.navigate(index)
        if index == 1:
            window.library_table.selectRow(0)
        if index == 3:
            window.flip_card()
        app.processEvents()
        window.grab().save(str(destination / (name + '.png')))
    window.close()
print('Screenshots captured using isolated synthetic demo data.')
