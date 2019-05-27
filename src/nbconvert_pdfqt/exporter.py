import sys
import os
import subprocess

from testpath.tempdir import TemporaryWorkingDirectory

import nbformat

from nbconvert.exporters.html import HTMLExporter


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
                "-m", "nbconvert_pdfqt.printer",
                td
            ], env=dict(
                **os.environ,
                QTWEBENGINE_DISABLE_SANDBOX="1",
                QT_WEBENGINE_DISABLE_GPU="1",
                QTWEBENGINE_CHROMIUM_FLAGS="--headless --disable-gpu --no-sandbox --single-process --enable-logging --log-level=0"
            ))

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
