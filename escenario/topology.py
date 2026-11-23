"""Topología de la figura 1 del enunciado: VMs, interfaces, IPs y rutas."""


def iface(bridge, address, routes=()):
    return {"bridge": bridge, "addr": address, "routes": list(routes)}


def route(destination, via):
    return {"to": destination, "via": via}


def specifications(num_servers):
    """Lista de (nombre, interfaces, reenvío IP) de todas las VMs."""
    specs = [
        ("c1", [iface("RED1", "10.0.10.2/26", [route("default", "10.0.10.1")])], False),
        ("fw", [
            iface("RED1", "10.0.10.1/26"),
            iface("RED2", "10.0.10.129/26", [route("10.0.10.64/26", "10.0.10.130")]),
        ], True),
        ("lb", [
            iface("RED2", "10.0.10.130/26", [route("default", "10.0.10.129")]),
            iface("RED3", "10.0.10.65/26"),
        ], True),
    ]
    for n in range(1, num_servers + 1):
        specs.append((
            f"s{n}",
            [iface("RED3", f"10.0.10.{65 + n}/26", [route("default", "10.0.10.65")])],
            False,
        ))
    return specs
