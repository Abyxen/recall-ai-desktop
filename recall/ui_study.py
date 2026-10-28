import json
import random

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QFormLayout, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPlainTextEdit,
    QScrollArea, QSpinBox, QSplitter, QVBoxLayout, QWidget)

from .study import Generator, edit_card, review_card, save_cards, save_quiz, submit_quiz
from .widgets import GenerationDialog, button, fill_table, label, panel, row, table


class StudyPages:
    def build_cards(self):
        layout = self.page('Flashcards', 'Build understanding, then keep it. Your ratings schedule the next review using an SM-2 variant.')
        self.deck_filter = QComboBox()
        self.deck_filter.currentIndexChanged.connect(lambda _: self.refresh_cards(False))
        self.due_only = QCheckBox('Due cards only')
        self.due_only.setChecked(True)
        self.due_only.toggled.connect(lambda _: self.refresh_cards(False))
        layout.addWidget(row(self.deck_filter, self.due_only, button('Shuffle', self.shuffle_cards), button('New card', lambda: self.card_dialog()), button('Generate deck', lambda: self.generate('cards'), True)))
        split = QSplitter(Qt.Orientation.Horizontal)
        self.cards_list = QListWidget()
        self.cards_list.currentItemChanged.connect(self.select_card)
        split.addWidget(self.cards_list)
        detail, content = panel()
        self.card_meta = label('Select a card to begin.', 'subtitle', True)
        self.card_question = label('Your next small step.', 'title', True)
        self.card_answer = QPlainTextEdit()
        self.card_answer.setReadOnly(True)
        self.card_answer.setPlaceholderText('Flip the card to reveal its answer and source.')
        content.addWidget(self.card_meta)
        content.addStretch()
        content.addWidget(self.card_question)
        content.addWidget(self.card_answer, 1)
        self.card_actions = [button('Flip card', self.flip_card, True), button('Edit', self.edit_current_card), button('Delete', self.delete_card)]
        content.addWidget(row(*self.card_actions))
        for control in self.card_actions:
            control.setEnabled(False)
        self.rating_buttons = []
        ratings = row()
        for title, rating in [('Again', 1), ('Hard', 3), ('Good', 4), ('Easy', 5)]:
            control = button(title, lambda checked=False, value=rating: self.rate_card(value))
            control.setEnabled(False)
            ratings.layout().addWidget(control)
            self.rating_buttons.append(control)
        content.addWidget(ratings)
        split.addWidget(detail)
        split.setSizes([300, 650])
        layout.addWidget(split, 1)

    def refresh_cards(self, decks=True):
        if not hasattr(self, 'cards_list'):
            return
        if decks:
            current = self.deck_filter.currentText()
            self.deck_filter.blockSignals(True)
            self.deck_filter.clear()
            self.deck_filter.addItem('All decks')
            self.deck_filter.addItems([r['deck'] for r in self.db.rows('SELECT DISTINCT deck FROM cards ORDER BY deck')])
            if current:
                self.deck_filter.setCurrentText(current)
            self.deck_filter.blockSignals(False)
        clauses, params = [], []
        if self.due_only.isChecked():
            clauses.append("due<=date('now','localtime')")
        if self.deck_filter.currentIndex() > 0:
            clauses.append('deck=?')
            params.append(self.deck_filter.currentText())
        rows = self.db.rows('SELECT * FROM cards' + (' WHERE ' + ' AND '.join(clauses) if clauses else '') + ' ORDER BY due,id', params)
        self.populate_cards(rows)

    def populate_cards(self, rows):
        self.cards_list.clear()
        for control in self.card_actions:
            control.setEnabled(bool(rows))
        for item in rows:
            widget = QListWidgetItem(item['question'] + '\n' + item['deck'] + ' · Due ' + item['due'])
            widget.setData(Qt.ItemDataRole.UserRole, item)
            self.cards_list.addItem(widget)
        if rows:
            self.cards_list.setCurrentRow(0)
        else:
            self.current_card = None
            self.card_question.setText('No cards in this view.')
            self.card_answer.clear()
            self.card_meta.setText('Generate a deck, create a card, or turn off the due-only filter.')
            for control in self.rating_buttons:
                control.setEnabled(False)

    def select_card(self, current, previous=None):
        self.current_card = current.data(Qt.ItemDataRole.UserRole) if current else None
        self.card_answer_visible = False
        self.card_answer.clear()
        for control in self.card_actions:
            control.setEnabled(bool(self.current_card))
        if self.current_card:
            card = self.current_card
            self.card_question.setText(card['question'])
            self.card_meta.setText(f"{card['deck']} · {card['difficulty']} · {card['topic']}\nDue {card['due']} · interval {card['interval']} days")
        for control in self.rating_buttons:
            control.setEnabled(False)

    def flip_card(self):
        if self.current_card:
            self.card_answer_visible = not self.card_answer_visible
            self.card_answer.setPlainText(self.current_card['answer'] + '\n\nSOURCE\n' + self.current_card['source'] if self.card_answer_visible else '')
            for control in self.rating_buttons:
                control.setEnabled(self.card_answer_visible)

    def rate_card(self, rating):
        if self.current_card and self.card_answer_visible:
            current_id = self.current_card['id']
            review_card(self.db, current_id, rating)
            self.refresh_cards(False)
            for i in range(self.cards_list.count()):
                if self.cards_list.item(i).data(Qt.ItemDataRole.UserRole)['id'] != current_id:
                    self.cards_list.setCurrentRow(i)
                    break

    def shuffle_cards(self):
        rows = [self.cards_list.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.cards_list.count())]
        random.shuffle(rows)
        self.populate_cards(rows)

    def card_dialog(self, card=None):
        dialog = QDialog(self)
        dialog.setWindowTitle('Edit flashcard' if card else 'New flashcard')
        dialog.resize(560, 450)
        form = QFormLayout(dialog)
        deck = QLineEdit(card['deck'] if card else 'My study deck')
        question = QPlainTextEdit(card['question'] if card else '')
        answer = QPlainTextEdit(card['answer'] if card else '')
        form.addRow('Deck', deck)
        form.addRow('Question', question)
        form.addRow('Answer', answer)
        controls = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        controls.accepted.connect(dialog.accept)
        controls.rejected.connect(dialog.reject)
        form.addRow(controls)
        if dialog.exec():
            try:
                if not deck.text().strip():
                    raise ValueError('Enter a deck name.')
                if card:
                    edit_card(self.db, card['id'], question.toPlainText(), answer.toPlainText(), deck.text())
                else:
                    if not 8 <= len(question.toPlainText().strip()) <= 2000 or not 2 <= len(answer.toPlainText().strip()) <= 4000:
                        raise ValueError('Use a question of 8–2,000 characters and an answer of 2–4,000 characters.')
                    save_cards(self.db, [dict(question=question.toPlainText().strip(), answer=answer.toPlainText().strip(), topic='Personal notes', difficulty='medium', source='User-created card')], deck.text())
                self.refresh_cards()
            except Exception as exc:
                self.error(exc)

    def edit_current_card(self):
        if self.current_card:
            self.card_dialog(self.current_card)

    def delete_card(self):
        if self.current_card and QMessageBox.question(self, 'Delete card', 'Delete this card? Review activity remains in your history.') == QMessageBox.StandardButton.Yes:
            self.db.execute('DELETE FROM cards WHERE id=?', (self.current_card['id'],))
            self.refresh_cards()

    def generate(self, kind):
        dialog = GenerationDialog(self.db, kind, self)
        if not dialog.exec():
            return
        title, options = dialog.title.text(), dialog.options()
        if not title.strip():
            self.error('Enter a deck or quiz title.')
            return
        def work():
            items = Generator(self.db).generate(kind, **options)
            return save_cards(self.db, items, title) if kind == 'cards' else save_quiz(self.db, title, items)
        def done(result):
            if kind == 'cards':
                self.due_only.setChecked(False)
                self.refresh_cards()
                self.deck_filter.setCurrentText(title.strip())
                QMessageBox.information(self, 'Deck saved', f'{result} new cards saved. Review generated answers against their source quotes.')
            else:
                self.refresh_quizzes()
                self.start_quiz(result)
        self.run_task('Generating and validating study material. This may take several minutes…', work, done)

    def build_quizzes(self):
        layout = self.page('Quizzes', 'Check your understanding. Objective answers use deterministic checking; free-text scores use a provisional phrase rubric.')
        self.quiz_minutes = QSpinBox()
        self.quiz_minutes.setRange(0, 180)
        self.quiz_minutes.setSuffix(' min (0 = untimed)')
        self.quiz_clock = label('Untimed', 'subtitle')
        self.quiz_start = button('Start / retake selected', self.start_selected_quiz)
        self.quiz_start.setEnabled(False)
        layout.addWidget(row(button('Generate quiz', lambda: self.generate('quiz'), True), self.quiz_start, self.quiz_minutes, self.quiz_clock))
        split = QSplitter(Qt.Orientation.Horizontal)
        self.quiz_list = QListWidget()
        self.quiz_list.currentItemChanged.connect(lambda current, previous: self.quiz_start.setEnabled(current is not None))
        split.addWidget(self.quiz_list)
        self.quiz_scroll = QScrollArea()
        self.quiz_scroll.setWidgetResizable(True)
        split.addWidget(self.quiz_scroll)
        split.setSizes([250, 700])
        layout.addWidget(split, 1)
        self.quiz_submit = button('Submit answers', self.submit_current_quiz, True)
        self.quiz_submit.setEnabled(False)
        layout.addWidget(self.quiz_submit)
        layout.addWidget(label('SAVED ATTEMPTS · SELECT A ROW TO REVIEW ANSWERS', 'eyebrow'))
        self.quiz_history = table(['Quiz', 'Score', 'Date (UTC)'])
        self.quiz_history.setMaximumHeight(145)
        self.quiz_history.itemSelectionChanged.connect(self.show_attempt)
        layout.addWidget(self.quiz_history)
        self.quiz_scroll.setWidget(label('Generate a quiz or retake a saved quiz.', wrap=True))

    def refresh_quizzes(self):
        self.quiz_list.clear()
        for item in self.db.rows('SELECT * FROM quizzes ORDER BY id DESC'):
            widget = QListWidgetItem(item['title'] + f"\n{len(json.loads(item['payload']))} questions")
            widget.setData(Qt.ItemDataRole.UserRole, item)
            self.quiz_list.addItem(widget)
        self.refresh_attempts()

    def refresh_attempts(self):
        attempts = self.db.rows('SELECT a.*,q.title,q.payload FROM attempts a JOIN quizzes q ON q.id=a.quiz_id ORDER BY a.id DESC LIMIT 50')
        self.quiz_history.blockSignals(True)
        fill_table(self.quiz_history, attempts, ['title', lambda r: f"{r['score']:.1f} / {r['total']}", 'created'])
        self.quiz_history.blockSignals(False)

    def start_selected_quiz(self):
        item = self.quiz_list.currentItem()
        if item:
            self.start_quiz(item.data(Qt.ItemDataRole.UserRole)['id'])

    def start_quiz(self, quiz_id):
        if self.current_quiz and self.quiz_submit.isEnabled():
            if QMessageBox.question(self, 'Replace quiz session', 'Discard current unsaved answers?') != QMessageBox.StandardButton.Yes:
                return
        self.quiz_timer.stop()
        self.current_quiz = self.db.rows('SELECT * FROM quizzes WHERE id=?', (quiz_id,))[0]
        body = QWidget()
        content = QVBoxLayout(body)
        content.setSpacing(18)
        content.addWidget(label(self.current_quiz['title'], 'title'))
        content.addWidget(label('Generated questions may contain mistakes. Check feedback against the source.', 'subtitle', True))
        self.quiz_inputs = []
        for i, item in enumerate(json.loads(self.current_quiz['payload']), 1):
            frame, group = panel()
            group.addWidget(label(f"{i}. {item['question']}", wrap=True))
            group.addWidget(label(item['type'].replace('_', ' ') + ' · ' + item['difficulty'], 'eyebrow'))
            if item['type'] in {'mcq', 'true_false'}:
                field = QComboBox()
                field.addItem('Choose your answer…', '')
                for option in item['options'] if item['type'] == 'mcq' else ['true', 'false']:
                    field.addItem(option, option)
            else:
                field = QPlainTextEdit()
                field.setMaximumHeight(100)
                field.setPlaceholderText('Decimal number only, in the requested units.' if item['type'] == 'calculation' else 'Your answer. Phrase-based scoring is provisional.')
            group.addWidget(field)
            self.quiz_inputs.append(field)
            content.addWidget(frame)
        content.addStretch()
        self.quiz_scroll.setWidget(body)
        self.quiz_submit.setEnabled(True)
        self.remaining_seconds = self.quiz_minutes.value() * 60
        self.quiz_clock.setText(f'{self.quiz_minutes.value()}:00 remaining' if self.remaining_seconds else 'Untimed')
        if self.remaining_seconds:
            self.quiz_timer.start(1000)

    def tick_quiz(self):
        self.remaining_seconds -= 1
        self.quiz_clock.setText(f'{self.remaining_seconds // 60}:{self.remaining_seconds % 60:02} remaining')
        if self.remaining_seconds <= 0:
            self.submit_current_quiz()

    def submit_current_quiz(self):
        if not self.current_quiz or not self.quiz_submit.isEnabled():
            return
        self.quiz_timer.stop()
        answers = [field.currentData() if isinstance(field, QComboBox) else field.toPlainText() for field in self.quiz_inputs]
        result = submit_quiz(self.db, self.current_quiz['id'], answers)
        self.quiz_submit.setEnabled(False)
        self.show_feedback(json.loads(self.current_quiz['payload']), answers, result)
        self.refresh_attempts()

    def show_feedback(self, items, answers, result):
        body = QWidget()
        content = QVBoxLayout(body)
        content.addWidget(label(f"{result['score']:.1f} / {result['total']} points", 'title'))
        content.addWidget(label('Free-text scores are provisional. Review missed answers and source evidence.', 'subtitle', True))
        for i, (item, answer, feedback) in enumerate(zip(items, answers, result['feedback']), 1):
            frame, group = panel()
            group.addWidget(label(f"{i}. {item['question']}", wrap=True))
            group.addWidget(label(f"{'Correct' if feedback['correct'] else 'Needs revision'} · {feedback['score']:.1f} / 1" + (' · provisional' if feedback['provisional'] else ''), 'eyebrow'))
            detail = QPlainTextEdit()
            detail.setReadOnly(True)
            detail.setPlainText(f"Your answer: {answer or '(blank)'}\nExpected: {feedback['expected']}\n\n{feedback['explanation']}\n\nChecking: {feedback['method']}\n\nSOURCE: {feedback['source']}\n{feedback['quote']}")
            detail.setMinimumHeight(210)
            group.addWidget(detail)
            content.addWidget(frame)
        content.addStretch()
        self.quiz_scroll.setWidget(body)

    def show_attempt(self):
        index = self.quiz_history.currentRow()
        if index < 0 or not self.quiz_history.item(index, 0) or self.quiz_submit.isEnabled():
            return
        attempt = self.quiz_history.item(index, 0).data(Qt.ItemDataRole.UserRole)
        result = dict(score=attempt['score'], total=attempt['total'], feedback=json.loads(attempt['feedback']))
        self.show_feedback(json.loads(attempt['payload']), json.loads(attempt['answers']), result)
