"""Shared pytest setup — isolate the app database before devcommandcenter
is imported anywhere in the test session (DATABASE_URL binds at import),
and create one offscreen QApplication for every test module to share."""

import os
import tempfile

_tmp_dir = tempfile.mkdtemp(prefix="dcc_pytest_")
os.environ.setdefault("DCC_DATABASE_URL", f"sqlite:///{_tmp_dir}/test.db")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

# A single application object for the whole session; test modules reuse it
# through QApplication.instance().
_app = QApplication.instance() or QApplication([])
