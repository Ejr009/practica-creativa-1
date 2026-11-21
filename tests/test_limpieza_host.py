import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1]


class TestLimpiezaHost(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_cwd = Path.cwd()
        os.chdir(self.tmp.name)

        for name in ("auto-p2.py", "lib_vm.py"):
            shutil.copy2(SOURCE / name, name)

        sys.path.insert(0, self.tmp.name)
        sys.modules.pop("lib_vm", None)

        spec = importlib.util.spec_from_file_location(
            "app_limpieza", "auto-p2.py"
        )
        self.app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.app)

    def tearDown(self):
        os.chdir(self.old_cwd)
        sys.path.remove(self.tmp.name)
        sys.modules.pop("lib_vm", None)
        self.tmp.cleanup()

    def test_fallos_y_recursos_ausentes(self):
        app = self.app

        state = {
            "created_by": "auto-p2.py",
            "vms": ["c1", "fw", "lb", "s1"],
            "bridges_added": ["RED1", "RED2", "RED3"],
            "host_address_added": True,
            "host_routes_added": ["10.0.10.128/26"],
        }

        class FakeVM:
            def __init__(self, name):
                pass

            def stop_vm(self):
                pass

            def state(self):
                return "shut off"

            def undefine_vm(self):
                pass

            def remove_files(self):
                pass

        class FakeNET:
            def __init__(self, name):
                pass

            def destroy_net(self):
                pass

        for mode in ("ruta_presente", "ip_presente", "ya_ausentes"):
            with self.subTest(mode=mode):
                app.save_state(state)

                def fake_exec(args, **kwargs):
                    code, out, err = 0, "", ""

                    if args[:4] == ["sudo", "ip", "route", "del"]:
                        if mode != "ip_presente":
                            code, err = 2, "Fallo simulado"

                    elif args[:4] == ["ip", "-4", "route", "show"]:
                        if mode == "ruta_presente":
                            out = "10.0.10.128/26 via 10.0.10.1 dev RED1"

                    elif args[:4] == ["sudo", "ip", "addr", "del"]:
                        code, err = 2, "Fallo simulado"

                    elif args[:4] == ["ip", "-4", "-o", "addr"]:
                        if mode == "ip_presente":
                            out = "4: RED1 inet 10.0.10.3/26 scope global RED1"

                    return subprocess.CompletedProcess(args, code, out, err)

                with patch.object(app, "VM", FakeVM), \
                     patch.object(app, "NET", FakeNET), \
                     patch.object(app, "ejecutar", side_effect=fake_exec):

                    if mode == "ya_ausentes":
                        app.undefine()
                        self.assertFalse(app.STATE.exists())
                    else:
                        with self.assertRaises(app.ErrorEscenario):
                            app.undefine()
                        self.assertTrue(app.STATE.exists())


if __name__ == "__main__":
    unittest.main()
