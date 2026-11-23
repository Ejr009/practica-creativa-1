"""Utilidades de prueba: directorio temporal con el código y sistema falso."""

import importlib
import importlib.util
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from fake_system import FakeSystem

SOURCE = Path(__file__).resolve().parents[1]
FILES = ("auto-p2.py", "lib_vm.py", "plantilla-vm-pc1.xml", "auto-p2.json")
PACKAGES = ("libvm", "escenario")


class EscenarioTestCase(unittest.TestCase):
    """Copia el código a un directorio temporal e importa los módulos allí."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="cdps_pc1_test_")
        self.work, self.old_cwd = Path(self.tmp.name), Path.cwd()
        os.chdir(self.work)
        for name in FILES:
            shutil.copy2(SOURCE / name, self.work / name)
        for package in PACKAGES:
            shutil.copytree(SOURCE / package, self.work / package)
        (self.work / "cdps-vm-base-pc1.qcow2").touch()
        sys.path.insert(0, str(self.work))
        self.purge()
        self.system = FakeSystem(self.work)
        patcher = patch("subprocess.run", self.system)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.cleanup)
        spec = importlib.util.spec_from_file_location("app", self.work / "auto-p2.py")
        self.app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.app)

    @staticmethod
    def purge():
        for name in list(sys.modules):
            if name.split(".")[0] in PACKAGES + ("lib_vm",):
                del sys.modules[name]

    def cleanup(self):
        os.chdir(self.old_cwd)
        sys.path.remove(str(self.work))
        self.purge()
        self.tmp.cleanup()

    def mod(self, name):
        return importlib.import_module(name)
