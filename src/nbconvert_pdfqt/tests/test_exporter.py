import nbformat
from nbconvert_pdfqt import PDFQtExporter

from nbformat.v4 import new_notebook


def test_exporter():
    exporter = PDFQtExporter()
    x = exporter.from_notebook_node(new_notebook())
    assert x
