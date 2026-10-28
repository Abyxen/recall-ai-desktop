import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout,
    QLineEdit, QMessageBox, QPlainTextEdit, QScrollArea, QSpinBox, QSplitter,
    QTextBrowser, QVBoxLayout, QWidget)

from .documents import ocr_available
from .provider import Provider
from .retrieval import source_label
from .tutor import Tutor
from .widgets import Scope, button, label, row


class TutorSettingsPages:
    def build_tutor(self):
        layout = self.page('AI Tutor', 'Ask questions grounded in your documents. Check explanations against the supporting source passages.')
        self.tutor_scope = Scope(self.db)
        self.tutor_scope.currentIndexChanged.connect(lambda _: self.refresh_conversations())
        self.tutor_level = QComboBox()
        self.tutor_level.addItems(['Beginner', 'Standard', 'Advanced'])
        self.tutor_level.setCurrentIndex(1)
        self.tutor_mode = QComboBox()
        self.tutor_mode.addItems(['Explain', 'Summary', 'Examples', 'Comparison', 'Key concepts', 'Revision notes'])
        layout.addWidget(row(self.tutor_scope, self.tutor_level, self.tutor_mode))
        self.conversation_picker = QComboBox()
        self.conversation_picker.activated.connect(self.load_conversation)
        self.followup = QCheckBox('Use recent conversation in this scope')
        self.followup.setChecked(True)
        layout.addWidget(row(self.conversation_picker, self.followup))
        self.tutor_status = label('Model connection not tested. Source retrieval also works without a model.', 'subtitle', True)
        layout.addWidget(self.tutor_status)
        split = QSplitter(Qt.Orientation.Horizontal)
        self.tutor_answer = QTextBrowser()
        self.tutor_answer.setOpenLinks(False)
        self.tutor_answer.setOpenExternalLinks(False)
        self.tutor_answer.setPlainText('What would you like to understand?\n\nImport a document, choose a scope, and ask a specific question.')
        self.tutor_evidence = QPlainTextEdit()
        self.tutor_evidence.setReadOnly(True)
        self.tutor_evidence.setPlaceholderText('Supporting passages will appear here with source positions.')
        split.addWidget(self.tutor_answer)
        split.addWidget(self.tutor_evidence)
        split.setSizes([600, 350])
        layout.addWidget(split, 1)
        self.question = QPlainTextEdit()
        self.question.setMaximumHeight(90)
        self.question.setPlaceholderText('Ask about your material…  Ctrl+Enter to send')
        layout.addWidget(self.question)
        layout.addWidget(button('Ask Recall', self.ask_tutor, True))

    def refresh_conversations(self):
        self.conversation_picker.clear()
        self.conversation_picker.addItem('Previous conversations in this scope…', None)
        scope = json.dumps(self.tutor_scope.currentData() or {}, sort_keys=True)
        for item in self.db.rows('SELECT * FROM conversations WHERE scope=? ORDER BY id DESC LIMIT 30', (scope,)):
            self.conversation_picker.addItem(item['question'][:85], item)

    def load_conversation(self):
        item = self.conversation_picker.currentData()
        if item:
            self.show_tutor_result(dict(answer=item['answer'], evidence=json.loads(item['evidence']), status='Saved conversation · check the evidence'))

    def show_tutor_result(self, result):
        self.tutor_answer.setMarkdown(result['answer'])
        self.tutor_status.setText(result['status'])
        self.tutor_evidence.setPlainText('\n\n'.join(f"[{i}] {source_label(r)}\n{r['text']}" for i, r in enumerate(result['evidence'], 1)) or 'No matching evidence.')

    def ask_tutor(self):
        if self.busy or self.stack.currentIndex() != 2:
            return
        question = self.question.toPlainText()
        scope, level, mode, followup = self.tutor_scope.currentData(), self.tutor_level.currentText(), self.tutor_mode.currentText(), self.followup.isChecked()
        def done(result):
            self.show_tutor_result(result)
            self.refresh_conversations()
        self.run_task('Retrieving evidence and asking your model…', lambda: Tutor(self.db).ask(question, scope, level, mode, followup), done)

    def build_settings(self):
        layout = self.page('Settings', 'Connect your own local model server. Recall never downloads model weights automatically.')
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        content = QVBoxLayout(body)
        form = QFormLayout()
        form.setSpacing(14)
        self.provider_kind = QComboBox()
        self.provider_kind.addItems(['ollama', 'openai'])
        self.provider_kind.setCurrentText(self.db.setting('provider', 'ollama'))
        self.endpoint = QLineEdit(self.db.setting('endpoint', 'http://localhost:11434'))
        self.model = QComboBox()
        self.model.setEditable(True)
        self.model.addItem(self.db.setting('model', 'axom:latest'))
        self.embedding_model = QLineEdit(self.db.setting('embedding_model', ''))
        self.embedding_model.setPlaceholderText('Blank = offline lexical vectors; semantic model is optional.')
        self.timeout = QSpinBox()
        self.timeout.setRange(10, 600)
        self.timeout.setValue(self.db.setting('timeout', 120))
        self.timeout.setSuffix(' seconds')
        self.temperature = QDoubleSpinBox()
        self.temperature.setRange(0, 1)
        self.temperature.setSingleStep(.1)
        self.temperature.setValue(self.db.setting('temperature', .2))
        self.external = QCheckBox('Allow sending document text and questions to this external endpoint')
        self.external.setChecked(self.db.setting('allow_external', False))
        self.ocr = QCheckBox('Enable optional local OCR for images / scanned PDF pages')
        self.ocr.setChecked(self.db.setting('ocr', False))
        self.library_dir = QLineEdit(self.db.setting('library_dir', str(self.db.home / 'library')))
        for name, field in [('Provider', self.provider_kind), ('Endpoint (OpenAI base URL includes /v1)', self.endpoint), ('Chat model', self.model), ('Embedding model', self.embedding_model), ('Timeout per request', self.timeout), ('Temperature', self.temperature), ('Library directory for new imports', self.library_dir)]:
            form.addRow(name, field)
        content.addLayout(form)
        content.addWidget(self.external)
        content.addWidget(self.ocr)
        content.addWidget(label('OCR: ' + ('Tesseract detected.' if ocr_available() else 'Tesseract not found on PATH. Text documents still work.'), 'subtitle', True))
        content.addWidget(label('Data directory: ' + str(self.db.home) + '\nChanging embedding settings requires re-indexing documents. Lexical vectors match words and have limited synonym understanding. Optional API key: RECALL_API_KEY environment variable. Local data is not encrypted.', 'subtitle', True))
        content.addWidget(row(button('Save settings', self.save_settings, True), button('Test connection / list models', self.test_connection), button('Model setup guide', self.model_guide)))
        self.connection_status = label('Connection has not been tested.', 'subtitle', True)
        content.addWidget(self.connection_status)
        content.addStretch()
        scroll.setWidget(body)
        layout.addWidget(scroll)

    def save_settings(self):
        values = dict(provider=self.provider_kind.currentText(), endpoint=self.endpoint.text().strip(), model=self.model.currentText().strip(),
                      embedding_model=self.embedding_model.text().strip(), timeout=self.timeout.value(), temperature=self.temperature.value(),
                      allow_external=self.external.isChecked(), ocr=self.ocr.isChecked(), library_dir=self.library_dir.text().strip())
        if not values['library_dir']:
            self.error('Choose a library directory.')
            return False
        class Preview:
            def setting(inner, key, default=None):
                return values.get(key, self.db.setting(key, default))
        try:
            Provider(Preview())
        except Exception as exc:
            self.error(exc)
            return False
        self.db.configure(**values)
        self.connection_status.setText('Settings saved. Test the connection to verify the selected model.')
        return True

    def test_connection(self):
        if not self.save_settings():
            return
        def done(models):
            current = self.model.currentText()
            self.model.clear()
            self.model.addItems(models)
            self.model.setCurrentText(current)
            self.connection_status.setText(f"Server reachable. {len(models)} model(s). Selected model " + ('is installed.' if current in models else 'not found; select an available model and Save.'))
        self.run_task('Testing model connection…', lambda: Provider(self.db).models(), done)

    def model_guide(self):
        QMessageBox.information(self, 'Local model setup', 'Install Ollama from https://ollama.com, then run ollama list. Select an installed instruct model and Test connection.\n\nOptional new model: manually run ollama pull qwen3:4b (several GB). Recall never downloads it.\n\nOptional semantic embeddings: manually install qwen3-embedding:0.6b, enter its name, save and re-index documents.\n\nOpenAI-compatible local servers: choose openai and a base URL ending in /v1.\n\nSee docs/MODEL_SETUP.md for details and troubleshooting.')
