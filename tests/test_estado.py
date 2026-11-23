"""Fichero de estado: guardado atómico, validación y selección de VMs."""

import json

from helpers import EscenarioTestCase


def valid_state(servers=1):
    return {"created_by": "auto-p2.py",
            "vms": ["c1", "fw", "lb"] + [f"s{i}" for i in range(1, servers + 1)],
            "bridges_added": ["RED1", "RED2", "RED3"],
            "host_address_added": True,
            "host_routes_added": ["10.0.10.128/26", "10.0.10.64/26"]}


class Estado(EscenarioTestCase):
    def setUp(self):
        super().setUp()
        self.state = self.mod("escenario.state")
        self.path = self.mod("escenario.settings").STATE
        self.error = self.mod("libvm.shell").ErrorEscenario

    def test_guardar_y_cargar(self):
        self.state.save_state(valid_state(3))
        self.assertEqual(self.state.load_state(), valid_state(3))
        self.assertFalse(self.path.with_name(self.path.name + ".tmp").exists())

    def test_rechaza_estados_invalidos(self):
        malos = [{"created_by": "otro"}, {**valid_state(), "vms": ["c1"]},
                 {**valid_state(), "vms": ["fw", "c1", "lb", "s1"]},
                 {**valid_state(), "bridges_added": ["RED9"]},
                 {**valid_state(), "bridges_added": ["RED1", "RED1"]},
                 {**valid_state(), "host_routes_added": ["0.0.0.0/0"]},
                 {**valid_state(), "host_address_added": "si"}]
        for bad in malos:
            self.path.write_text(json.dumps(bad))
            with self.assertRaises(self.error):
                self.state.load_state()

    def test_json_corrupto_o_ausente(self):
        with self.assertRaises(self.error):
            self.state.load_state()
        self.path.write_text("{no es json")
        with self.assertRaises(self.error):
            self.state.load_state()

    def test_select_vms(self):
        state = valid_state(2)
        self.assertEqual(self.state.select_vms(state, None), state["vms"])
        self.assertEqual(self.state.select_vms(state, "s2"), ["s2"])
        with self.assertRaises(self.error):
            self.state.select_vms(state, "s9")
