import sys
import os
from uuid import uuid4
import socket
import time
import subprocess

from six.moves.urllib.request import urlopen

from PyQt5 import QtCore, QtWidgets, QtWebEngineWidgets, QtGui

from .static import SINGLE_DOCUMENT, RUN_ALL, LAB_STYLE, FORCE_DEV


class QPDFPage(QtWebEngineWidgets.QWebEnginePage):
    dpi = None
    scale_hack = 2.5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.loadFinished.connect(self._load_finished)
        self.loadProgress.connect(self._load_progress)
        self.setZoomFactor(1)

    def _load_progress(self, *args):
        print("progress")
        self.runJavaScript(FORCE_DEV)

    def _load_finished(self, finished):
        print("finished")
        self.runJavaScript(f"""
            var style = document.createElement("style");
            style.textContent = `{LAB_STYLE}`;
            document.body.appendChild(style);
            {SINGLE_DOCUMENT % 2000}
            {RUN_ALL}
        """)
        QtCore.QTimer.singleShot(8000, lambda *_: self.measure())

    def measure(self):
        print("measuring")
        self.runJavaScript(f"""
            var bb = document.querySelector(".jp-Cell:last-child").getBoundingClientRect();
            var node = document.querySelector(".jp-ApplicationShell").style;
            var body = document.body.style;
            node.height = node.minHeight = body.height = body.minHeight = bb.bottom + "px";
            {SINGLE_DOCUMENT % 0}
            [bb.bottom, bb.right]
        """, lambda size: self.emit_pdf(size))

    def emit_pdf(self, size):
        margins = QtCore.QMarginsF(15, 15, 15, 15)
        layout = QtGui.QPageLayout(QtGui.QPageSize(QtGui.QPageSize.A4),
                                   QtGui.QPageLayout.Portrait,
                                   margins)
        self.printToPdf(
            os.path.join(os.getcwd(), "notebook.pdf"),
            layout
        )
        print("emitted")


def print_pdf():
    host = "localhost"
    token = str(uuid4())

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, 0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()

    lab = subprocess.Popen([
        sys.executable,
        "-m",
        "jupyterlab.labapp",
        "--port={}".format(port),
        "--NotebookApp.token='{}'".format(token),
        "--no-browser"
    ])
    url = "http://{}:{}/lab/tree/notebook.ipynb?token={}".format(host, port, token)
    shutdown_url = "http://{}:{}/api/shutdown?token={}".format(host, port, token)

    retries = 10

    while retries:
        time.sleep(1)
        retries -= 1
        try:
            urlopen(url)
            break
        except:
            pass

    app = QtWidgets.QApplication([])
    screen = app.screens()[0]

    page = QPDFPage()
    page.dpi = screen.physicalDotsPerInch()

    def shutdown():
        try:
            urlopen(shutdown_url, data=[])
        except:
            pass
        finally:
            lab.wait()
        try:
            app.quit()
        except:
            pass

    page.pdfPrintingFinished.connect(lambda *_: shutdown())
    page.load(QtCore.QUrl(url))

    try:
        app.exec_()
    finally:
        shutdown()


if __name__ == "__main__":
    print_pdf()
