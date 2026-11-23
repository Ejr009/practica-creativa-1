"""Ficheros cloud-init (meta-data, network-config, user-data) y su ISO."""

from libvm.shell import ejecutar


# La imagen del laboratorio no siempre instala al arrancar las rutas que netplan
# genera bien; se reaplica netplan tras systemd-networkd, también en reinicios.
NETPLAN_SERVICE = [
    "  - path: /etc/systemd/system/cdps-netplan-apply.service",
    "    permissions: '0644'",
    "    content: |",
    "      [Unit]",
    "      Description=CDPS reapply Netplan after boot",
    "      After=systemd-networkd.service",
    "      Wants=systemd-networkd.service",
    "      [Service]",
    "      Type=oneshot",
    "      ExecStart=/usr/sbin/netplan apply",
    "      [Install]",
    "      WantedBy=multi-user.target",
]
FORWARD_FILE = [
    "  - path: /etc/sysctl.d/99-cdps-ipforward.conf",
    "    permissions: '0644'",
    "    content: |",
    "      net.ipv4.ip_forward=1",
]


def meta_data(name):
    return f"instance-id: {name}-id\nlocal-hostname: {name}\n"


def network_config(interfaces):
    lines = ["version: 2", "ethernets:"]
    for index, iface in enumerate(interfaces):
        lines += [f"  eth{index}:", "    dhcp4: false", "    dhcp6: false",
                  "    link-local: []", "    addresses:", f"      - {iface['addr']}"]
        routes = iface.get("routes", [])
        if routes:
            lines.append("    routes:")
        for route in routes:
            lines += [f"      - to: {route['to']}", f"        via: {route['via']}"]
    return "\n".join(lines) + "\n"


def user_data(name, forwarding, files, commands):
    """files: pares (ruta, contenido); commands: listas de comando extra."""
    lines = ["#cloud-config", f"hostname: {name}", "manage_etc_hosts: true",
             "write_files:"] + NETPLAN_SERVICE
    if forwarding:
        lines += FORWARD_FILE
    for path, content in files:
        lines += [f"  - path: {path}", "    permissions: '0644'", "    content: |"]
        lines += ["      " + line for line in content.splitlines()]
    lines += ["runcmd:", "  - [systemctl, daemon-reload]",
              "  - [systemctl, enable, cdps-netplan-apply.service]",
              "  - [netplan, apply]"]
    if forwarding:
        lines.append("  - [sysctl, -p, /etc/sysctl.d/99-cdps-ipforward.conf]")
    lines += ["  - [" + ", ".join(cmd) + "]" for cmd in commands]
    return "\n".join(lines) + "\n"


def write_cloud_init(vm, interfaces, forwarding, files=(), commands=()):
    """Escribe los tres ficheros NoCloud de la VM y crea su ISO."""
    vm.cloud_dir.mkdir(parents=True, exist_ok=True)
    contenido = {
        "meta-data": meta_data(vm.name),
        "network-config": network_config(interfaces),
        "user-data": user_data(vm.name, forwarding, files, commands),
    }
    for nombre, texto in contenido.items():
        (vm.cloud_dir / nombre).write_text(texto, encoding="utf-8")
    ejecutar(["genisoimage", "-quiet", "-output", vm.iso, "-volid", "cidata",
              "-joliet", "-rock", "user-data", "meta-data", "network-config"],
             cwd=vm.cloud_dir)
