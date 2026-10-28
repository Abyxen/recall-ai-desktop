import json
import time
from PySide6.QtWidgets import QApplication, QMessageBox
from recall.study import Generator, save_cards, save_quiz
from recall.ui import MainWindow
from recall.smoke import offline_workflow


def test_offline_packaging_workflow():
    assert offline_workflow()


def test_desktop_workflow(material, item):
    app = QApplication.instance() or QApplication([])
    db = material['db']
    sources = {material['source']['id']: dict(material['source'], name='Biology.txt')}
    generated = Generator.validate(item, 'quiz', sources, ['mcq'])
    save_cards(db, [generated], 'Plants')
    quiz_id = save_quiz(db, 'Plants quiz', [generated])
    window = MainWindow(db)
    window.show()
    for index in range(7):
        window.navigate(index)
        app.processEvents()
        assert window.stack.currentIndex() == index
    window.navigate(1)
    window.library_table.selectRow(0)
    assert 'Photosynthesis' in window.document_preview.toPlainText()
    window.navigate(3)
    assert window.cards_list.count() == 1
    window.flip_card()
    assert 'sunlight' in window.card_answer.toPlainText()
    window.rate_card(4)
    assert window.cards_list.count() == 0
    window.navigate(4)
    window.start_quiz(quiz_id)
    window.quiz_inputs[0].setCurrentIndex(1)
    window.submit_current_quiz()
    assert db.rows('SELECT score FROM attempts')[0]['score'] == 1
    assert window.quiz_history.rowCount() == 1
    window.quiz_minutes.setValue(1)
    window.start_quiz(quiz_id)
    window.remaining_seconds = 1
    window.tick_quiz()
    assert len(db.rows('SELECT * FROM attempts')) == 2
    assert not window.quiz_timer.isActive()
    window.close()
    restarted = MainWindow(db)
    restarted.navigate(0)
    assert restarted.stat_labels['cards'].text() == '1'
    assert restarted.stat_labels['due'].text() == '0'
    restarted.close()


def test_background_import_and_model_failure(db, tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    path = tmp_path / 'Study.txt'
    path.write_text('Chlorophyll absorbs sunlight during photosynthesis.', encoding='utf-8')
    window = MainWindow(db)
    window.show()
    messages = []
    monkeypatch.setattr(QMessageBox, 'information', lambda *args: messages.append(args[-1]))
    window.organization_dialog = lambda: ['Biology', 'Plants']
    window.import_files([str(path)])
    deadline = time.monotonic() + 10
    while window.busy and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(.01)
    assert not window.busy and window.library_table.rowCount() == 1
    assert '1 document(s)' in messages[0]
    window.navigate(2)
    window.question.setPlainText('What does chlorophyll absorb?')
    window.ask_tutor()
    deadline = time.monotonic() + 10
    while window.busy and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(.01)
    assert not window.busy and 'evidence only' in window.tutor_status.text()
    assert 'Chlorophyll' in window.tutor_evidence.toPlainText()
    window.close()
