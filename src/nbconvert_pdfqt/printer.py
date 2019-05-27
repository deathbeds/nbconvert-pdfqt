import sys
import os
from uuid import uuid4
import socket


from PyQt5 import QtCore, QtWidgets, QtWebEngineWidgets, QtGui

from .lab import LabProcess
from .static import SINGLE_DOCUMENT, APPLY_STYLE, FORCE_DEV, MEASURE


class QPDFPage(QtWebEngineWidgets.QWebEnginePage):
    dpi = None
    scale_hack = 2.5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setZoomFactor(1)

        self.loadFinished.connect(self._load_finished)
        self.loadProgress.connect(self._load_progress)

    def _load_progress(self, *args):
        self.runJavaScript(FORCE_DEV)

    def _load_finished(self, finished):
        self.runJavaScript(APPLY_STYLE)
        QtCore.QTimer.singleShot(8000, lambda *_: self._measure())

    def _measure(self):
        self.runJavaScript(MEASURE, lambda size: self._emit_pdf(size))

    def _emit_pdf(self, size):
        margins = QtCore.QMarginsF(15, 15, 15, 15)
        layout = QtGui.QPageLayout(QtGui.QPageSize(QtGui.QPageSize.A4),
                                   QtGui.QPageLayout.Portrait,
                                   margins)
        self.printToPdf(
            os.path.join(os.getcwd(), "notebook.pdf"),
            layout
        )

def print_pdf():
    app = QtWidgets.QApplication([])
    screen = app.screens()[0]

    page = QPDFPage()
    page.dpi = screen.physicalDotsPerInch()

    lab = LabProcess()
    lab.start()
    lab.ready()

    def shutdown():
        lab.stop()
        app.quit()

    page.pdfPrintingFinished.connect(lambda *_: shutdown())
    page.load(QtCore.QUrl(lab.notebook_url))

    try:
        app.exec_()
    finally:
        shutdown()


if __name__ == "__main__":
    print_pdf()
