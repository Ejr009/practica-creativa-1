"""Órdenes define, start, stop, monitor y undefine sobre el sistema simulado."""

import contextlib
import io
from unittest.mock import patch

from helpers import EscenarioTestCase


class Comandos(EscenarioTestCase):
    def setUp(self):
        super().setUp()
        self.settings = self.mod("escenario.settings")
        self.consoles = patch("lib_vm.open_console")
        self.consoles.start()
        self.addCleanup(self.consoles.stop)

    def define(self, n=2):
        self.mod("escenario.cmd_define").define(n)

    def test_define_crea_todo_apagado(self):
        self.define(2)
        self.assertEqual(set(self.system.domains), {"c1", "fw", "lb", "s1", "s2"})
        self.assertEqual(set(self.system.domains.values()), {"shut off"})
        self.assertEqual(self.system.bridges, {"RED1", "RED2", "RED3"})
        self.assertEqual(self.system.addresses, ["10.0.10.3/26"])
        self.assertTrue(self.settings.STATE.exists())

    def test_define_dos_veces_falla(self):
        self.define(1)
        with self.assertRaises(self.mod("libvm.shell").ErrorEscenario):
            self.define(1)

    def test_start_y_stop_de_una_vm(self):
        self.define(2)
        self.mod("escenario.cmd_start").start("s1")
        self.assertEqual(self.system.domains["s1"], "running")
        self.assertEqual(self.system.domains["s2"], "shut off")
        self.mod("escenario.cmd_stop").stop("s1")
        self.assertEqual(self.system.domains["s1"], "shut off")

    def test_start_arranca_routers_antes_que_servidores(self):
        self.define(2)
        self.mod("escenario.cmd_start").start()
        starts = [c.split()[-1] for c in self.system.calls if " start " in c]
        self.assertEqual(starts, ["fw", "lb", "c1", "s1", "s2"])

    def test_monitor_muestra_estado_y_ping(self):
        self.define(1)
        self.mod("escenario.cmd_start").start("c1")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.mod("escenario.cmd_monitor").monitor()
        text = out.getvalue()
        self.assertIn("c1   running     10.0.10.2     ok", text)
        self.assertIn("fw   shut off", text)

    def test_undefine_libera_todo(self):
        self.define(2)
        self.mod("escenario.cmd_start").start()
        self.mod("escenario.cmd_undefine").undefine()
        self.assertEqual((self.system.domains, self.system.bridges), ({}, set()))
        self.assertEqual((self.system.addresses, self.system.routes), ([], []))
        self.assertFalse(self.settings.STATE.exists())
        self.assertEqual(list(self.work.glob("*.qcow2")),
                         [self.work / "cdps-vm-base-pc1.qcow2"])
