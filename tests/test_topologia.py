"""Topología, configuración JSON, servicios y ficheros cloud-init/XML."""

import json
import xml.etree.ElementTree as ET

from helpers import EscenarioTestCase


class Topologia(EscenarioTestCase):
    def test_direccionamiento_1_a_5_servidores(self):
        topo = self.mod("escenario.topology")
        for n in range(1, 6):
            specs = topo.specifications(n)
            self.assertEqual(len(specs), 3 + n)
            self.assertEqual(specs[0][1][0]["addr"], "10.0.10.2/26")
            self.assertEqual(specs[1][1][1]["addr"], "10.0.10.129/26")
            self.assertEqual(specs[2][1][1]["addr"], "10.0.10.65/26")
            self.assertEqual(specs[-1][1][0]["addr"], f"10.0.10.{65 + n}/26")

    def test_solo_fw_y_lb_reenvian(self):
        specs = self.mod("escenario.topology").specifications(2)
        self.assertEqual([n for n, _, fwd in specs if fwd], ["fw", "lb"])

    def test_json_limites(self):
        config = self.mod("escenario.config")
        path = self.mod("escenario.settings").CONFIG
        for n in range(1, 6):
            path.write_text(json.dumps({"num_servers": n}))
            self.assertEqual(config.read_config()["num_servers"], n)
        error = self.mod("libvm.shell").ErrorEscenario
        for bad in (0, 6, -1, True, 1.5, "3", None):
            path.write_text(json.dumps({"num_servers": bad}))
            with self.assertRaises(error):
                config.read_config()

    def test_servicios_apache_y_haproxy(self):
        services = self.mod("escenario.services").services
        self.assertIn("Servidor s2", services("s2", 3)["files"][0][1])
        cfg = services("lb", 3)["files"][0][1]
        for n in (1, 2, 3):
            self.assertIn(f"server s{n} 10.0.10.{65 + n}:80 check", cfg)
        self.assertIn("bind *:8404", cfg)
        self.assertEqual(services("fw", 3), {})


class FicherosVm(EscenarioTestCase):
    def define_fw(self):
        topo = self.mod("escenario.topology").specifications(1)
        name, interfaces, forwarding = topo[1]
        vm = self.mod("lib_vm").VM(name)
        vm.define_vm(self.work / "cdps-vm-base-pc1.qcow2", interfaces,
                     forwarding=forwarding)
        return vm

    def test_cloud_init_con_reenvio_y_rutas(self):
        vm = self.define_fw()
        user = (vm.cloud_dir / "user-data").read_text()
        net = (vm.cloud_dir / "network-config").read_text()
        self.assertIn("net.ipv4.ip_forward=1", user)
        self.assertIn("- to: 10.0.10.64/26", net)
        self.assertIn("via: 10.0.10.130", net)

    def test_xml_con_una_interfaz_por_red(self):
        vm = self.define_fw()
        bridges = [i.find("source").get("bridge")
                   for i in ET.parse(vm.xml).getroot().iter("interface")]
        self.assertEqual(bridges, ["RED1", "RED2"])

    def test_define_rechaza_vm_existente(self):
        vm = self.define_fw()
        with self.assertRaises(self.mod("libvm.shell").ErrorEscenario):
            vm.define_vm(self.work / "cdps-vm-base-pc1.qcow2", [{"bridge": "RED1", "addr": "1.1.1.1/26"}])
