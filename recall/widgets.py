from PySide6.QtCore import QObject, QRunnable, Qt, Signal
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QDialog, QDialogButtonBox,
    QFormLayout, QFrame, QHeaderView, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit,
    QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)


def label(text, name=None, wrap=False):
    item = QLabel(text)
    if name:
        item.setObjectName(name)
    item.setWordWrap(wrap)
    return item


def button(text, callback, primary=False):
    item = QPushButton(text)
    if primary:
        item.setObjectName('primary')
    item.clicked.connect(callback)
    return item


def row(*items):
    widget = QWidget()
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(10)
    for item in items:
        layout.addWidget(item)
    return widget


def panel():
    widget = QFrame()
    widget.setObjectName('panel')
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(20, 18, 20, 18)
    layout.setSpacing(12)
    return widget, layout


def table(headers):
    widget = QTableWidget(0, len(headers))
    widget.setHorizontalHeaderLabels(headers)
    widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    widget.setAlternatingRowColors(True)
    widget.verticalHeader().hide()
    widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    return widget


def fill_table(widget, rows, columns):
    widget.setRowCount(len(rows))
    for i, item in enumerate(rows):
        for j, key in enumerate(columns):
            cell = QTableWidgetItem(str(key(item) if callable(key) else item[key]))
            cell.setData(Qt.ItemDataRole.UserRole, item)
            widget.setItem(i, j, cell)


class WorkerSignals(QObject):
    result = Signal(object)
    error = Signal(str)
    done = Signal()


class Worker(QRunnable):
    def __init__(self, function):
        super().__init__()
        self.function = function
        self.signals = WorkerSignals()

    def run(self):
        try:
            self.signals.result.emit(self.function())
        except Exception as exc:
            self.signals.error.emit(str(exc))
        finally:
            self.signals.done.emit()


class Scope(QComboBox):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setMinimumWidth(170)
        self.refresh()

    def refresh(self):
        previous = self.currentData()
        self.blockSignals(True)
        self.clear()
        self.addItem('Entire library', {})
        for item in self.db.rows('SELECT DISTINCT subject FROM documents ORDER BY subject'):
            self.addItem('Subject · ' + item['subject'], item)
        for item in self.db.rows('SELECT DISTINCT subject,notebook FROM documents ORDER BY subject,notebook'):
            self.addItem(item['subject'] + ' / ' + item['notebook'], item)
        for item in self.db.rows('SELECT id,name FROM documents ORDER BY name'):
            self.addItem('Document · ' + item['name'], {'document_id': item['id']})
        for i in range(self.count()):
            if self.itemData(i) == previous:
                self.setCurrentIndex(i)
                break
        self.blockSignals(False)


class GenerationDialog(QDialog):
    def __init__(self, db, kind, parent):
        super().__init__(parent)
        self.setWindowTitle('Generate flashcards' if kind == 'cards' else 'Generate quiz')
        self.resize(560, 520)
        layout = QVBoxLayout(self)
        layout.addWidget(label('Create from your sources', 'title'))
        layout.addWidget(label('Review generated content for accuracy before studying. Quotes are checked against the source text.', 'subtitle', True))
        form = QFormLayout()
        self.scope = Scope(db)
        self.title = QLineEdit('My study deck' if kind == 'cards' else 'Practice quiz')
        self.topic = QLineEdit()
        self.topic.setPlaceholderText('Optional chapter or topic')
        self.passage = QPlainTextEdit()
        self.passage.setPlaceholderText('Optional exact passage from an indexed chunk')
        self.passage.setMaximumHeight(80)
        self.count = QSpinBox()
        self.count.setRange(1, 20)
        self.count.setValue(5)
        self.difficulty = QComboBox()
        self.difficulty.addItems(['easy', 'medium', 'hard'])
        self.difficulty.setCurrentIndex(1)
        self.types = QComboBox()
        self.types.addItems(['Mixed', 'Multiple choice', 'True / false', 'Short answer', 'Conceptual explanation', 'Calculation (verify solution)'])
        for name, field in [('Source', self.scope), ('Deck / quiz title', self.title), ('Topic', self.topic), ('Exact passage', self.passage), ('Items', self.count), ('Difficulty', self.difficulty)]:
            form.addRow(name, field)
        if kind == 'quiz':
            form.addRow('Question type', self.types)
        layout.addLayout(form)
        controls = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        controls.button(QDialogButtonBox.StandardButton.Ok).setText('Generate')
        controls.accepted.connect(self.accept)
        controls.rejected.connect(self.reject)
        layout.addWidget(controls)

    def options(self):
        types = [['mcq', 'true_false', 'short_answer'], ['mcq'], ['true_false'], ['short_answer'], ['explanation'], ['calculation']]
        return dict(scope=self.scope.currentData(), topic=self.topic.text(), passage=self.passage.toPlainText(), count=self.count.value(), difficulty=self.difficulty.currentText(), question_types=types[self.types.currentIndex()])
