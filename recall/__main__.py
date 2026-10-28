import sys
from PySide6.QtWidgets import QApplication
from .db import Database
from .ui import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('Recall AI')
    app.setOrganizationName('RecallAI')
    window = MainWindow(Database())
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
