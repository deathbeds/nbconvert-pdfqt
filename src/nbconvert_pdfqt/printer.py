import sys
import os
from uuid import uuid4
import socket
import time
import subprocess

from six.moves.urllib.request import urlopen

from PyQt5 import QtCore, QtWidgets, QtWebEngineWidgets, QtGui


LAB_STYLE = """
body {
    --jp-layout-color0: transparent;
    --jp-layout-color1: transparent;
    --jp-layout-color2: transparent;
    --jp-layout-color3: transparent;
    --jp-cell-editor-background: transparent;
    --jp-border-width: 0;
    --jp-border-color0: transparent;
    --jp-border-color1: transparent;
    --jp-border-color2: transparent;
}
body,
body .jp-ApplicationShell {
    width: 1920px;
    height: 2024px;
}
body .jp-InputArea-editor {
    border: 0;
    padding-left: 2em;
}
body .jp-LabShell.jp-mod-devMode {
    border: 0 !important;
}
body .jp-InputPrompt,
body .jp-OutputPrompt {
    display: none;
    min-width: 0;
    max-width: 0;
}
body #jp-main-dock-panel {
    padding: 0;
}
body .jp-SideBar.p-TabBar,
body #jp-top-panel,
body .jp-Toolbar,
body .p-DockPanel-tabBar,
body .jp-Collapser {
    display: none;
    min-height: 0;
    max-height: 0;
    min-width: 0;
    max-width: 0;
}
"""

FORCE_DEV = """
var cfg = document.querySelector("#jupyter-config-data");
if(cfg) {
    cfg.textContent = cfg.textContent.replace(
        `"devMode": "False"`,
        `"devMode": "True"`
    )
}
"""

SINGLE_DOCUMENT = """
window.lab.shell.removeClass('jp-mod-devMode');
let cmd = window.lab.commands;
setTimeout(function(){
    cmd.execute('application:set-mode', {mode: 'single-document'});
    if(document.querySelector('body[data-left-sidebar-widget]')) {
        cmd.execute('application:toggle-left-area');
    }
}, 2000);
setTimeout(function(){
    console.error('running all cells');
    cmd.execute('notebook:run-all-cells');
}, 3000);
"""


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
            {SINGLE_DOCUMENT}
        """)
        QtCore.QTimer.singleShot(8000, lambda *_: self.measure())

    def measure(self):
        print("measuring")
        self.runJavaScript(f"""
            var bb = document.querySelector(".jp-Cell:last-child").getBoundingClientRect();
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
