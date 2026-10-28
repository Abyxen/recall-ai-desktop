import json
from PySide6.QtWidgets import QApplication
from recall.study import Generator, save_cards, save_quiz
from recall.ui import MainWindow


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
    window.close()
    restarted = MainWindow(db)
    restarted.navigate(0)
    assert restarted.stat_labels['cards'].text() == '1'
    assert restarted.stat_labels['due'].text() == '0'
    restarted.close()
