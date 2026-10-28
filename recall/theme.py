STYLE = """
QWidget { background:#11151e; color:#e9edf5; font-family:'Segoe UI'; font-size:14px; }
QFrame#sidebar { background:#0b1018; border-right:1px solid #252d3c; }
QLabel#brand { font-size:27px; font-weight:700; }
QLabel#eyebrow { color:#9aa9c0; font-size:11px; font-weight:600; }
QLabel#title { font-size:29px; font-weight:700; }
QLabel#subtitle { color:#9aa9c0; }
QLabel#stat { font-size:34px; font-weight:700; color:#c8bdff; }
QFrame#panel { background:#191f2b; border:1px solid #2a3345; border-radius:14px; }
QFrame#panel QLabel { background:transparent; }
QPushButton { background:#252e40; border:1px solid #35415a; border-radius:7px; padding:9px 15px; font-weight:600; }
QPushButton:hover { background:#33415b; border-color:#8e80df; }
QPushButton:disabled { color:#758096; background:#1a202b; }
QPushButton#primary { background:#b4a2fc; color:#17122d; border-color:#b4a2fc; }
QPushButton#primary:hover { background:#c8baff; }
QPushButton#nav { text-align:left; padding:13px 18px; border:0; background:transparent; color:#9eabc0; }
QPushButton#nav:checked { background:#27243d; color:#d2c6ff; }
QLineEdit,QPlainTextEdit,QTextBrowser,QComboBox,QSpinBox,QDoubleSpinBox { background:#141b27; border:1px solid #344057; border-radius:7px; padding:8px; selection-background-color:#65558f; }
QLineEdit:focus,QPlainTextEdit:focus { border-color:#b4a2fc; }
QComboBox QAbstractItemView { background:#20283a; selection-background-color:#4b416c; }
QTableWidget,QListWidget { background:#161d29; border:1px solid #2a3345; border-radius:8px; alternate-background-color:#1b2331; gridline-color:#283247; }
QTableWidget::item,QListWidget::item { padding:10px; }
QTableWidget::item:selected,QListWidget::item:selected { background:#393250; color:#f1ecff; }
QHeaderView::section { background:#1f2839; padding:10px; border:0; color:#a9b7ce; font-weight:600; }
QScrollArea { border:0; }
QScrollBar:vertical { background:#151c28; width:10px; }
QScrollBar::handle:vertical { background:#3d4860; border-radius:5px; min-height:30px; }
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical { height:0; }
QProgressBar { border:0; background:#242d3f; border-radius:4px; text-align:center; }
QProgressBar::chunk { background:#a491ed; border-radius:4px; }
QCheckBox { spacing:8px; }
QStatusBar { color:#9aa9c0; border-top:1px solid #252d3c; }
"""
