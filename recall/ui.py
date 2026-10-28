from __future__ import annotations

from datetime import date, timedelta
import os
from pathlib import Path

from PySide6.QtCore import Qt, QThreadPool, QTimer
from PySide6.QtGui import QAction, QFontDatabase
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
    QComboBox, QFrame, QHBoxLayout, QLineEdit, QMainWindow, QMessageBox, QPlainTextEdit,
    QProgressBar, QStackedWidget, QVBoxLayout, QWidget)

from .documents import SUPPORTED
from .library import Library
from .metrics import dashboard
from .retrieval import source_label
from .theme import STYLE
from .ui_study import StudyPages
from .ui_tutor import TutorSettingsPages
from .widgets import Worker, button, fill_table, label, panel, row, table


class MainWindow(StudyPages, TutorSettingsPages, QMainWindow):
    def __init__(self, db):
        super().__init__()
        # Qt's Windows offscreen plugin does not discover system fonts itself.
        for name in ('segoeui.ttf', 'segoeuib.ttf'):
            font = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts' / name
            if font.exists():
                QFontDatabase.addApplicationFont(str(font))
        self.db = db
        self.pool = QThreadPool(self)
        self.busy = False
        self.current_card = None
        self.current_quiz = None
        self.quiz_inputs = []
        self.quiz_timer = QTimer(self)
        self.quiz_timer.timeout.connect(self.tick_quiz)
        self.setWindowTitle('Recall AI — Your private study workspace')
        self.resize(1320, 860)
        self.setMinimumSize(1020, 700)
        self.setStyleSheet(STYLE)
        self.setAcceptDrops(True)
        outer = QWidget()
        horizontal = QHBoxLayout(outer)
        horizontal.setContentsMargins(0, 0, 0, 0)
        horizontal.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName('sidebar')
        sidebar.setFixedWidth(224)
        nav = QVBoxLayout(sidebar)
        nav.setContentsMargins(20, 30, 20, 22)
        nav.setSpacing(7)
        nav.addWidget(label('recall', 'brand'))
        nav.addWidget(label('AI STUDY WORKSPACE', 'eyebrow'))
        nav.addSpacing(30)
        self.nav = []
        for i, title in enumerate(['Dashboard', 'My Library', 'AI Tutor', 'Flashcards', 'Quizzes', 'Progress', 'Settings']):
            control = button(title, lambda checked=False, index=i: self.navigate(index))
            control.setObjectName('nav')
            control.setCheckable(True)
            nav.addWidget(control)
            self.nav.append(control)
        nav.addStretch()
        nav.addWidget(label('LOCAL FIRST', 'eyebrow'))
        nav.addWidget(label('Your notes. Your pace.\nStored on this device.', 'subtitle', True))
        horizontal.addWidget(sidebar)
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(15)
        self.busy_bar = QProgressBar()
        self.busy_bar.setRange(0, 0)
        self.busy_bar.setMaximumHeight(4)
        self.busy_bar.hide()
        layout.addWidget(self.busy_bar)
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        horizontal.addWidget(body, 1)
        self.setCentralWidget(outer)
        for build in [self.build_dashboard, self.build_library, self.build_tutor, self.build_cards, self.build_quizzes, self.build_progress, self.build_settings]:
            build()
        self.statusBar().showMessage('Ready · Data is local. Model connection has not been tested.')
        self.navigate(0)
        for shortcut, callback in [('Ctrl+O', self.import_files), ('Ctrl+Return', self.ask_tutor), ('Ctrl+1', lambda: self.navigate(0)), ('Ctrl+2', lambda: self.navigate(1)), ('Ctrl+3', lambda: self.navigate(2))]:
            action = QAction(self)
            action.setShortcut(shortcut)
            action.triggered.connect(callback)
            self.addAction(action)

    def page(self, title, subtitle):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(label(title, 'title'))
        layout.addWidget(label(subtitle, 'subtitle', True))
        self.stack.addWidget(widget)
        return layout

    def navigate(self, index):
        self.stack.setCurrentIndex(index)
        for i, control in enumerate(self.nav):
            control.setChecked(i == index)
        if index == 0:
            self.refresh_dashboard()
        elif index == 1:
            self.refresh_library()
        elif index == 2:
            self.tutor_scope.refresh()
            self.refresh_conversations()
        elif index == 3:
            self.refresh_cards()
        elif index == 4:
            self.refresh_quizzes()
        elif index == 5:
            self.refresh_progress()

    def error(self, message):
        QMessageBox.warning(self, 'Recall AI', str(message))

    def run_task(self, title, function, callback):
        if self.busy:
            return
        self.busy = True
        self.stack.setEnabled(False)
        self.busy_bar.show()
        self.statusBar().showMessage(title)
        worker = Worker(function)
        worker.signals.result.connect(callback)
        worker.signals.error.connect(self.error)
        worker.signals.done.connect(self.task_done)
        self.worker = worker
        self.pool.start(worker)

    def task_done(self):
        self.busy = False
        self.stack.setEnabled(True)
        self.busy_bar.hide()
        self.statusBar().showMessage('Ready · Operation finished. Check any reported errors.')

    def closeEvent(self, event):
        if self.busy:
            self.error('An operation is running. Wait for it to finish before closing Recall AI.')
            event.ignore()
        else:
            event.accept()

    def build_dashboard(self):
        layout = self.page('Make room for understanding.', 'Turn your course material into small, focused study sessions.')
        layout.addWidget(row(button('Import documents', self.import_files, True), button('Ask your AI tutor', lambda: self.navigate(2)), button('Review due cards', self.open_due_cards)))
        stats = row()
        self.stat_labels = {}
        for name, key in [('Documents', 'documents'), ('Notebooks', 'notebooks'), ('Flashcards', 'cards'), ('Due for review', 'due')]:
            card, content = panel()
            value = label('0', 'stat')
            self.stat_labels[key] = value
            content.addWidget(label(name, 'subtitle'))
            content.addWidget(value)
            stats.layout().addWidget(card)
        layout.addWidget(stats)
        frame, content = panel()
        content.addWidget(label('YOUR NEXT STEP', 'eyebrow'))
        self.next_action = label('', wrap=True)
        content.addWidget(self.next_action)
        layout.addWidget(frame)
        layout.addWidget(label('RECENTLY ADDED', 'eyebrow'))
        self.recent_docs = table(['Document', 'Subject', 'Notebook', 'Source units'])
        layout.addWidget(self.recent_docs, 1)
        layout.addWidget(label('RECENT QUIZ RESULTS', 'eyebrow'))
        self.recent_quizzes = table(['Quiz', 'Result', 'Date (UTC)'])
        self.recent_quizzes.setMaximumHeight(160)
        layout.addWidget(self.recent_quizzes)

    def refresh_dashboard(self):
        data = dashboard(self.db)
        for key, item in self.stat_labels.items():
            item.setText(str(data[key]))
        due_text = '1 card is ready' if data['due'] == 1 else f"{data['due']} cards are ready"
        self.next_action.setText('Add your first document to start your study library.' if not data['documents'] else f"{due_text} for review. A short session now helps you remember more later." if data['due'] else 'Choose a document, ask a question, or generate your next study deck.')
        fill_table(self.recent_docs, data['recent_documents'], ['name', 'subject', 'notebook', 'pages'])
        fill_table(self.recent_quizzes, data['recent_attempts'], ['title', lambda r: f"{r['score']:.1f} / {r['total']}", 'created'])

    def build_library(self):
        layout = self.page('My Library', 'Drop files anywhere in Recall. Originals are preserved; copied files and extracted text stay in your local library.')
        self.library_search = QLineEdit()
        self.library_search.setPlaceholderText('Search document, subject or notebook…')
        self.library_search.textChanged.connect(self.refresh_library)
        layout.addWidget(row(self.library_search, button('Import documents', self.import_files, True)))
        layout.addWidget(label('PDF · DOCX · PPTX · TXT · MARKDOWN · IMAGES WITH OPTIONAL OCR', 'eyebrow'))
        self.library_table = table(['Document', 'Subject', 'Notebook', 'Units', 'Status'])
        self.library_table.itemSelectionChanged.connect(self.show_document)
        layout.addWidget(self.library_table, 3)
        self.library_actions = [button('Organize', self.organize_document), button('Re-index', self.reindex_document), button('Remove from library', self.remove_document)]
        for control in self.library_actions:
            control.setEnabled(False)
        layout.addWidget(row(*self.library_actions))
        self.document_preview = QPlainTextEdit()
        self.document_preview.setReadOnly(True)
        self.document_preview.setPlaceholderText('Select a document to preview indexed text and source positions.')
        layout.addWidget(self.document_preview, 2)

    def selected_document(self):
        index = self.library_table.currentRow()
        cell = self.library_table.item(index, 0) if index >= 0 else None
        return cell.data(Qt.ItemDataRole.UserRole) if cell else None

    def refresh_library(self):
        search = '%' + self.library_search.text().strip() + '%'
        rows = self.db.rows('SELECT * FROM documents WHERE name LIKE ? OR subject LIKE ? OR notebook LIKE ? ORDER BY id DESC', (search, search, search))
        fill_table(self.library_table, rows, ['name', 'subject', 'notebook', 'pages', 'status'])

    def show_document(self):
        doc = self.selected_document()
        for control in self.library_actions:
            control.setEnabled(bool(doc))
        if not doc:
            self.document_preview.clear()
            return
        chunks = self.db.rows('SELECT * FROM chunks WHERE document_id=? ORDER BY id LIMIT 30', (doc['id'],))
        self.document_preview.setPlainText('\n\n'.join(f"{source_label(dict(c, name=doc['name']))}\n{c['text']}" for c in chunks))

    def organization_dialog(self, subject='General', notebook='Notes'):
        dialog = QDialog(self)
        dialog.setWindowTitle('Choose subject and notebook')
        form = QFormLayout(dialog)
        fields = []
        for key, current in [('subject', subject), ('notebook', notebook)]:
            combo = QComboBox()
            combo.setEditable(True)
            combo.addItems([r[key] for r in self.db.rows(f'SELECT DISTINCT {key} FROM documents ORDER BY {key}')])
            combo.setCurrentText(current)
            form.addRow(key.capitalize(), combo)
            fields.append(combo)
        controls = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        controls.accepted.connect(dialog.accept)
        controls.rejected.connect(dialog.reject)
        form.addRow(controls)
        if dialog.exec():
            values = [field.currentText().strip() for field in fields]
            if all(values):
                return values
            self.error('Subject and notebook cannot be empty.')
        return None

    def import_files(self, paths=None):
        if self.busy:
            return
        if not isinstance(paths, list):
            paths, _ = QFileDialog.getOpenFileNames(self, 'Import course material', '', 'Study documents (' + ' '.join('*' + s for s in sorted(SUPPORTED)) + ')')
        if not paths:
            return
        organization = self.organization_dialog()
        if not organization:
            return
        def work():
            successes, errors = 0, []
            for path in paths:
                try:
                    Library(self.db).import_file(path, *organization)
                    successes += 1
                except Exception as exc:
                    errors.append(f'{Path(path).name}: {exc}')
            return successes, errors
        def done(result):
            self.navigate(1)
            QMessageBox.information(self, 'Import complete', f'{result[0]} document(s) imported.' + ('\n\n' + '\n'.join(result[1]) if result[1] else ''))
        self.run_task(f'Importing {len(paths)} document(s)…', work, done)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and not self.busy:
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
        if paths:
            event.acceptProposedAction()
            self.import_files(paths)

    def organize_document(self):
        doc = self.selected_document()
        if doc:
            values = self.organization_dialog(doc['subject'], doc['notebook'])
            if values:
                Library(self.db).organize(doc['id'], *values)
                self.refresh_library()

    def reindex_document(self):
        doc = self.selected_document()
        if doc:
            self.run_task('Re-indexing document…', lambda: Library(self.db).reindex(doc['id']), lambda _: self.refresh_library())

    def remove_document(self):
        doc = self.selected_document()
        if doc and QMessageBox.question(self, 'Remove document', 'Remove this document and index? Study cards/history, managed copies and original files are retained.') == QMessageBox.StandardButton.Yes:
            Library(self.db).remove(doc['id'])
            self.refresh_library()

    def build_progress(self):
        layout = self.page('Progress', 'A record of your actual study activity. Free-text quiz marks are provisional.')
        self.progress_summary = label('', 'subtitle', True)
        layout.addWidget(self.progress_summary)
        frame, content = panel()
        content.addWidget(label('LAST 7 DAYS · CARD REVIEWS + QUIZ ATTEMPTS', 'eyebrow'))
        self.activity_rows = []
        for offset in range(6, -1, -1):
            day = date.today() - timedelta(days=offset)
            bar = QProgressBar()
            bar.setMinimumHeight(22)
            self.activity_rows.append((day.isoformat(), bar))
            day_label = label(day.strftime('%a %d %b'))
            day_label.setFixedWidth(105)
            content.addWidget(row(day_label, bar))
        layout.addWidget(frame)
        layout.addWidget(label('TOPICS NEEDING REVISION · BELOW 80% IN UP TO 100 RECENT ATTEMPTS', 'eyebrow', True))
        self.weak_table = table(['Topic', 'Average', 'Questions answered'])
        layout.addWidget(self.weak_table, 1)
        layout.addWidget(button('Review due cards', self.open_due_cards, True))

    def open_due_cards(self):
        self.navigate(3)
        self.deck_filter.setCurrentIndex(0)
        self.due_only.setChecked(True)
        self.refresh_cards(False)

    def refresh_progress(self):
        data = dashboard(self.db)
        self.progress_summary.setText(f"{data['reviews']} card reviews · {data['attempts']} quiz attempts · {data['due']} cards due today")
        maximum = max(data['activity'].values(), default=1)
        for day, bar in self.activity_rows:
            value = data['activity'].get(day, 0)
            bar.setRange(0, max(1, maximum))
            bar.setValue(value)
            bar.setFormat(f'{value} study actions')
        rows = [dict(topic=t, average=f'{a:.0%}', count=n) for t, a, n in data['weak_topics']]
        fill_table(self.weak_table, rows, ['topic', 'average', 'count'])
