"""Servicios que arranca cloud-init: Apache en los servidores y HAProxy en LB."""

HAPROXY_CFG = """global
    stats socket /run/haproxy/admin.sock mode 660 level admin
defaults
    mode http
    timeout connect 5s
    timeout client 30s
    timeout server 30s
frontend web
    bind *:80
    default_backend servers
backend servers
    balance roundrobin
{servers}listen stats
    bind *:8404
    stats enable
    stats uri /stats
    stats admin if TRUE
"""


def services(name, num_servers):
    """Ficheros y comandos extra de cloud-init para la VM indicada."""
    if name.startswith("s"):
        return {"files": [("/var/www/html/index.html", f"<h1>Servidor {name}</h1>\n")],
                "commands": [["systemctl", "enable", "--now", "apache2"]]}
    if name == "lb":
        servers = "".join(f"    server s{n} 10.0.10.{65 + n}:80 check\n"
                          for n in range(1, num_servers + 1))
        return {"files": [("/etc/haproxy/haproxy.cfg", HAPROXY_CFG.format(servers=servers))],
                "commands": [["systemctl", "enable", "--now", "haproxy"]]}
    return {}
