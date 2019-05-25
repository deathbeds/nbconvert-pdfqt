import sys
import os
import subprocess

from testpath.tempdir import TemporaryWorkingDirectory

import nbformat

from nbconvert.exporters.html import HTMLExporter

LAB_STYLE = """
body {
    --jp-layout-color0: transparent;
    --jp-layout-color1: transparent;
    --jp-layout-color2: transparent;
    --jp-layout-color3: transparent;
    --jp-cell-editor-background: transparent;
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
body .jp-SideBar.p-TabBar {
    min-width: 0;
    max-width: 0;
    display: none;
}
body #jp-top-panel {
    display: none;
    min-height: 0;
    max-height: 0;
}
body .jp-Toolbar {
    display: none;
    min-height: 0;
    max-height: 0;
}
body .p-DockPanel-tabBar {
    display: none;
    min-height: 0;
    max-height: 0;
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

class PDFQtExporter(HTMLExporter):
    def from_notebook_node(self, nb, resources=None, **kw):
        """ Generate a PDF from a given parsed notebook node
        """
        output, resources = super(PDFQtExporter, self).from_notebook_node(
            nb, resources=resources, **kw
        )

        with TemporaryWorkingDirectory() as td:
            for path, res in resources.get("outputs", {}).items():
                dest = os.path.join(td, os.path.basename(path))
                shutil.copyfile(path, dest)

            index_html = os.path.join(td, "index.html")

            with open(index_html, "w+") as fp:
                fp.write(output)

            ipynb = "notebook.ipynb"

            with open(os.path.join(td, ipynb), "w") as fp:
                nbformat.write(nb, fp)

            self.log.info("Building PDF...")

            subprocess.check_call([
                sys.executable,
                "-m", "nbconvert_pdfqt.exporter",
                td
            ])

            pdf_file = "notebook.pdf"

            if not os.path.isfile(pdf_file):
                raise IOError("PDF creating failed")

            self.log.info("PDF successfully created")

            with open(pdf_file, 'rb') as f:
                pdf_data = f.read()

        # convert output extension to pdf
        # the writer above required it to be tex
        resources['output_extension'] = '.pdf'
        # clear figure outputs, extracted by pdf export,
        # so we don't claim to be a multi-file export.
        resources.pop('outputs', None)

        return pdf_data, resources


def print_pdf():
    from uuid import uuid4
    import socket
    import time

    from six.moves.urllib.request import urlopen

    from PyQt5 import QtCore, QtWidgets, QtWebEngineWidgets, QtGui

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

    app = QtWidgets.QApplication(["-platform", "offscreen"])
    web = QtWebEngineWidgets.QWebEngineView()

    def started(*args):
        web.page().runJavaScript(FORCE_DEV)

    def wait_for_content(finished):
        web.show()
        web.page().runJavaScript(f"""
            var style = document.createElement("style");
            style.textContent = `{LAB_STYLE}`;
            document.body.appendChild(style);
            {SINGLE_DOCUMENT}
        """)
        web.setFixedSize(1000, 10000)
        QtCore.QTimer.singleShot(8000, measure)

    def measure():
        web.page().runJavaScript(f"""
            var bb = document.querySelector(".jp-Cell:last-child").getBoundingClientRect();
            [bb.bottom, bb.right]
        """, emit_pdf)

    def emit_pdf(size):
        screen = app.screens()[0]
        dpi = screen.physicalDotsPerInch()
        print("SIZE", size, dpi)
        x = 2.5
        dims = size[0] / dpi * x, size[1] / dpi * x
        page_size = QtGui.QPageSize(QtCore.QSizeF(*dims), QtGui.QPageSize.Inch)
        layout = QtGui.QPageLayout()
        layout.setPageSize(page_size)

        web.page().printToPdf(
            os.path.join(os.getcwd(), "notebook.pdf"),
            layout
        )

    def emitted_pdf(*args):
        app.quit()

    web.loadProgress.connect(started)
    web.loadFinished.connect(wait_for_content)
    web.page().pdfPrintingFinished.connect(emitted_pdf)

    web.load(QtCore.QUrl(url))

    try:
        app.exec_()
    finally:
        urlopen(shutdown_url, data=[])
        lab.wait()

if __name__ == "__main__":
    print_pdf()
