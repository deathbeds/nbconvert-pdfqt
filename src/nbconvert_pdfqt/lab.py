import os
import socket
import subprocess
import sys
import time

from urllib.error import URLError
from urllib.request import urlopen
from uuid import uuid4



class LabProcess(object):
    host = None
    port = None
    notebook = "notebook.ipynb"
    lab_cmd = [sys.executable, "-m", "jupyterlab.labapp"]
    proc = None
    retries = 20

    def __init__(self, host=None, port=None, notebook=None, token=None):
        self.host = host or "localhost"
        self.port = port or self.unused_port()
        self.notebook = notebook or "notebook.ipynb"
        self.token = token or str(uuid4())

    def start(self):
        self.stop()

        self.proc = subprocess.Popen([
            *self.lab_cmd,
            "--port={}".format(self.port),
            "--NotebookApp.token='{}'".format(self.token),
            "--no-browser"
        ])

    def stop(self):
        if self.proc is None:
            return 0

        try:
            urlopen(self.shutdown_url, data=[])
        except URLError:
            self.proc.terminate()
            self.proc.terminate()
            time.sleep(2)
            self.proc.terminate(kill=True)
        finally:
            rc = self.proc.wait()
            self.proc = None

        return rc

    @property
    def notebook_url(self):
        return "http://{}:{}/lab/tree/{}?token={}".format(
            self.host,
            self.port,
            self.notebook,
            self.token
        )

    @property
    def shutdown_url(self):
        return "http://{}:{}/api/shutdown?token={}".format(
            self.host,
            self.port,
            self.token
        )

    def ready(self):
        for i in range(self.retries):
            try:
                urlopen(self.notebook_url)
                return True
            except URLError:
                time.sleep(0.5)
        return False

    def unused_port(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((self.host, 0))
        sock.listen(1)
        port = sock.getsockname()[1]
        sock.close()
        return port
