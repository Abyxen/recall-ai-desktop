import sys
import json
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from .db import Database
from .ui import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('Recall AI')
    app.setOrganizationName('RecallAI')
    window = MainWindow(Database())
    window.show()
    if '--smoke-test' in sys.argv:
        def check():
            marker = window.db.home / 'smoke-result.json'
            try:
                from .smoke import offline_workflow
                for index in range(7):
                    window.navigate(index)
                passed = offline_workflow()
                marker.write_text(json.dumps({'launched': window.isVisible(), 'pages': window.stack.count(), 'offline_workflow': passed}), encoding='utf-8')
                app.quit()
            except Exception as exc:
                marker.write_text(json.dumps({'error': str(exc)}), encoding='utf-8')
                app.exit(1)
        QTimer.singleShot(500, check)
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
