"""Packaged entry point with an inspectable startup error log."""
import os
from pathlib import Path
import sys
import traceback

if __name__ == '__main__':
    try:
        from recall.__main__ import main
        main()
    except Exception:
        root = Path(os.environ.get('RECALL_DATA_DIR', str(Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'RecallAI')))
        root.mkdir(parents=True, exist_ok=True)
        message = traceback.format_exc()
        (root / 'startup-error.log').write_text(message, encoding='utf-8')
        if sys.stderr:
            sys.stderr.write(message)
        sys.exit(1)
