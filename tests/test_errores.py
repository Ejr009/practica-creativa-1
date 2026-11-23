"""Fallos: rollback de define, errores de OVS/virsh y CLI."""

import io
import json
from unittest.mock import patch

from helpers import EscenarioTestCase


class Errores(EscenarioTestCase):
    def setUp(self):
        super().setUp()
        self.error = self.mod("libvm.shell").ErrorEscenario
        self.settings = self.mod("escenario.settings")

    def define(self, n=2):
        self.mod("escenario.cmd_define").define(n)

    def test_fallo_en_define_hace_rollback(self):
        self.system.fail.add("virsh define " + str(self.work / "s2.xml"))
        with self.assertRaises(self.error):
            self.define(2)
        self.assertEqual((self.system.domains, self.system.bridges), ({}, set()))
        self.assertEqual((self.system.addresses, self.system.routes), ([], []))
        self.assertFalse(self.settings.STATE.exists())
        self.assertEqual(list(self.work.glob("*.xml")), [self.work / "plantilla-vm-pc1.xml"])

    def test_rollback_fallido_conserva_estado(self):
        self.system.fail.update({"virsh define " + str(self.work / "s1.xml"),
                                 "ovs-vsctl del-br"})
        with self.assertRaises(self.error) as ctx:
            self.define(1)
        self.assertIn("Conservamos el estado", str(ctx.exception))
        self.assertTrue(self.settings.STATE.exists())

    def test_ovs_distingue_ausencia_de_error(self):
        net = self.mod("libvm.net").NET("RED1")
        self.assertFalse(net.exists())
        self.system.fail.add("br-exists")
        with self.assertRaises(self.error):
            net.exists()

    def test_virsh_distingue_ausencia_de_error(self):
        vm = self.mod("lib_vm").VM("c1")
        self.assertIsNone(vm.state())
        self.system.fail.add("virsh list")
        with self.assertRaises(self.error):
            vm.state()

    def test_no_se_anota_bridge_si_falla_el_guardado(self):
        with patch("escenario.bridges.save_state", side_effect=self.error("disco")):
            with self.assertRaises(self.error):
                self.define(1)
        self.assertEqual(self.system.bridges, set())

    def test_undefine_con_json_roto(self):
        self.define(1)
        self.settings.CONFIG.write_text("{roto")
        with patch("sys.argv", ["auto-p2.py", "undefine"]):
            self.assertEqual(self.app.main(), 0)
        self.assertEqual(self.system.domains, {})

    def test_cli_rechaza_orden_o_vm_invalida(self):
        for argv in (["x"], ["define", "s1"], ["undefine", "s1"]):
            with patch("sys.argv", ["auto-p2.py"] + argv), \
                    patch("sys.stderr", io.StringIO()), self.assertRaises(SystemExit):
                self.app.main()

    def test_define_con_json_invalido_devuelve_1(self):
        self.settings.CONFIG.write_text(json.dumps({"num_servers": 9}))
        with patch("sys.argv", ["auto-p2.py", "define"]):
            self.assertEqual(self.app.main(), 1)
