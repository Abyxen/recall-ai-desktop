from PySide6.QtWidgets import QApplication, QFileDialog, QLabel, QListWidget, QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget
from .library import Library


class MainWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle('Recall AI')
        self.resize(1100, 740)
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.addWidget(QLabel('Recall AI · Your private study workspace'))
        button = QPushButton('Import documents')
        button.clicked.connect(self.import_files)
        layout.addWidget(button)
        self.documents = QListWidget()
        layout.addWidget(self.documents)
        self.setCentralWidget(root)
        self.refresh()

    def refresh(self):
        self.documents.clear()
        for row in self.db.rows('SELECT * FROM documents ORDER BY id DESC'):
            self.documents.addItem(f"{row['name']} · {row['pages']} pages · {row['subject']} / {row['notebook']}")

    def import_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, 'Import documents')
        for path in files:
            try:
                Library(self.db).import_file(path)
            except Exception as exc:
                QMessageBox.warning(self, 'Import failed', str(exc))
        self.refresh()
