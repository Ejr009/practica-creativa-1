"""Sistema falso: simula virsh, Open vSwitch e ip sin tocar la máquina."""

from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET


class FakeSystem:
    """Simula los comandos del sistema; `fail` fuerza errores por texto."""

    def __init__(self, work):
        self.work, self.fail, self.calls = work, set(), []
        self.bridges, self.domains = set(), {}
        self.addresses, self.routes = [], []

    def __call__(self, args, **kwargs):
        args = [a for a in map(str, args) if a != "sudo"]
        line = " ".join(args)
        self.calls.append(line)
        if any(text in line for text in self.fail):
            return self.done(1, err="fallo simulado")
        return self.dispatch(args, line, kwargs.get("cwd"))

    @staticmethod
    def done(code=0, out="", err=""):
        return subprocess.CompletedProcess([], code, out, err)

    def dispatch(self, a, line, cwd):
        if a[0] == "ovs-vsctl":
            return self.ovs(a)
        if a[0] == "virsh":
            return self.virsh(a)
        if a[0] == "ip":
            return self.ip(a, line)
        if a[0] == "qemu-img":
            Path(a[-1]).touch()
        if a[0] == "genisoimage":
            Path(a[a.index("-output") + 1]).touch()
        return self.done()

    def ovs(self, a):
        cmd, name = a[1], a[2]
        if cmd == "br-exists":
            return self.done(0 if name in self.bridges else 2)
        (self.bridges.add if cmd == "add-br" else self.bridges.discard)(name)
        return self.done()

    def virsh(self, a):
        cmd = a[1]
        if cmd == "list":
            return self.done(out="\n".join(self.domains) + "\n")
        if cmd == "define":
            self.domains[ET.parse(a[2]).getroot().find("name").text] = "shut off"
            return self.done()
        name = a[2]
        if name not in self.domains:
            return self.done(1, err="dominio no encontrado")
        new = {"start": "running", "shutdown": "shut off"}
        if cmd == "domstate":
            return self.done(out=self.domains[name] + "\n")
        if cmd == "undefine":
            del self.domains[name]
        else:
            self.domains[name] = new[cmd]
        return self.done()

    def ip(self, a, line):
        if "addr show" in line:
            return self.done(out="".join(f"2: RED1 inet {x}\n" for x in self.addresses))
        if "route show" in line:
            return self.done(out="".join(f"{r} via 10.0.10.1 dev RED1\n"
                                         for r in self.routes if r == a[-1]))
        if a[1] == "addr":
            (self.addresses.append if a[2] == "add" else self.addresses.remove)(a[3])
        if a[1] == "route":
            (self.routes.append if a[2] == "add" else self.routes.remove)(a[3])
        return self.done()
