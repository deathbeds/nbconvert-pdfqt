import sys
import os
from uuid import uuid4
import socket


from PyQt5 import QtCore, QtWidgets, QtWebEngineWidgets, QtGui, QtWebChannel

from .lab import LabProcess
from .static import SINGLE_DOCUMENT, APPLY_STYLE, FORCE_DEV, MEASURE, BRIDGE


class QPDFPage(QtWebEngineWidgets.QWebEnginePage):
    dpi = None
    scale_hack = 2.5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setZoomFactor(1)

        self.loadFinished.connect(self._load_finished)
        self.loadProgress.connect(self._load_progress)
        self.profile().scripts().insert(self._qwc_script())
        self.channel = QtWebChannel.QWebChannel(self)
        self.setWebChannel(self.channel)
        self.channel.registerObject('page', self)

    def _qwc_js(self):
        qfile = QtCore.QFile(':/qtwebchannel/qwebchannel.js')
        qfile.open(QtCore.QIODevice.ReadOnly)
        return bytes(qfile.readAll()).decode('utf-8')

    def _qwc_script(self):
        script = QtWebEngineWidgets.QWebEngineScript()
        script.setSourceCode(f"""
            {self._qwc_js()}
            {BRIDGE}
        """)
        script.setName('xxx')
        script.setWorldId(QtWebEngineWidgets.QWebEngineScript.MainWorld)
        script.setInjectionPoint(QtWebEngineWidgets.QWebEngineScript.DocumentReady)
        script.setRunsOnSubFrames(True)
        return script

    def javaScriptConsoleMessage(self, level, msg, linenumber, source_id):
        try:
            print('%s:%s: %s' % (source_id, linenumber, msg))
        except OSError:
            pass

    @QtCore.pyqtSlot(str)
    def print(self, text):
        print('From JS:', text)

    def _load_progress(self, *args):
        self.runJavaScript(FORCE_DEV)

    def _load_finished(self, finished):
        self.runJavaScript(APPLY_STYLE)

    @QtCore.pyqtSlot()
    def _measure(self):
        self.runJavaScript(MEASURE, lambda size: self._emit_pdf(size))

    def _emit_pdf(self, size):
        margins = QtCore.QMarginsF(0, 0, 0, 0)
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
