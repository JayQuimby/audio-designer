"""Application entry point."""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from . import assets


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Voice Assist")
    if missing := assets.missing_assets():
        QMessageBox.critical(
            None,
            "Voice Assist",
            "Some model files are missing. Run  python scripts/fetch_assets.py  to restore them:\n\n"
            + "\n".join(str(p) for p in missing),
        )
        return 1
    from .ui.main_window import MainWindow

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
