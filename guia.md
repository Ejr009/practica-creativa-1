# Guía rápida: instalar y probar todo

Todos los comandos están para copiar y pegar, en orden, desde el servidor del laboratorio (UDS) con entorno gráfico. Cada bloque tiene un comentario con lo que debe ocurrir.

## 1. Preparar (una vez)

**Paso 0: evita el error de pegado.** Algunos terminales marcan lo que pegas con `^[[200~` al principio y una `~` al final, y eso rompe el comando. Desactívalo una vez por terminal:

```bash
bind 'set enable-bracketed-paste off'
```

Después, un comando por línea (sin `&&` ni comentarios):

```bash
/lab/cnvr/bin/prepare-vnx-debian
mkdir -p ~/pc1
cd ~/pc1
git clone https://github.com/Ejr009/practica-creativa-1.git
cd practica-creativa-1
cp /lab/cdps/pc1/cdps-vm-base-pc1.qcow2 .
ls
```

Qué hace cada uno: `prepare-vnx-debian` prepara KVM y Open vSwitch; `mkdir` y `cd` crean y entran en la carpeta de trabajo; `git clone` baja el código; `cp` trae la imagen base (no está en Git). El `ls` debe mostrar: `auto-p2.py lib_vm.py libvm/ escenario/ auto-p2.json plantilla-vm-pc1.xml cdps-vm-base-pc1.qcow2`.

Sin Git: `wget https://github.com/Ejr009/practica-creativa-1/archive/refs/heads/main.zip` y `unzip main.zip`.

## 2. Configurar (número de servidores, de 1 a 5)

```bash
cat > auto-p2.json <<'EOF'
{
  "num_servers": 3,
  "debug": false
}
EOF
```

Para ver los comandos que ejecuta el script, cambia `false` por `true`.

## 3. Desplegar y arrancar

```bash
python3 auto-p2.py define     # crea bridges, discos, cloud-init, XML y define las VMs
python3 auto-p2.py start      # arranca las VMs y abre una consola por VM

# Espera a que termine cloud-init y HAProxy responda (puede tardar unos minutos):
until curl -s -o /dev/null --max-time 2 http://10.0.10.130/; do sleep 5; done; echo "LISTO"
```

## 4. Comprobar que todo funciona

```bash
# Estado de todas las VMs (con ping desde el host). Refresco continuo: watch -n2 python3 auto-p2.py monitor
python3 auto-p2.py monitor

# Estado de libvirt y de los bridges
sudo virsh list --all
sudo ovs-vsctl list-br

# Conectividad IP entre redes (el host está en RED1 con rutas hacia RED2 y RED3)
for ip in 10.0.10.2 10.0.10.1 10.0.10.129 10.0.10.130 10.0.10.65 10.0.10.66; do
  ping -c1 -W1 $ip >/dev/null && echo "$ip ok" || echo "$ip SIN RESPUESTA"
done

# Balanceo: debe alternar s1, s2, s3...
for i in 1 2 3 4 5 6; do curl -s http://10.0.10.130/; done

# Gestión de HAProxy: estado de los servidores en texto (UP/DOWN) y por web
curl -s "http://10.0.10.130:8404/stats;csv" | cut -d, -f1,2,18 | grep -E "^servers"
echo "Web: http://10.0.10.130:8404/stats"
```

Desde una consola de C1 también debes hacer `ping 10.0.10.66`, y desde S1 `ping 10.0.10.2`. Si necesitas entrar en una VM, usa las credenciales de la imagen del laboratorio (las de la práctica 2); allí `cloud-init status` debe decir `done`.

## 5. Parar y arrancar una sola VM

```bash
python3 auto-p2.py stop s1          # apagado ordenado solo de s1
sleep 10
for i in 1 2 3 4; do curl -s http://10.0.10.130/; done   # ya no responde s1
python3 auto-p2.py monitor          # s1 aparece "shut off"

python3 auto-p2.py start s1         # vuelve a arrancar solo s1
sleep 60
for i in 1 2 3 4; do curl -s http://10.0.10.130/; done   # s1 vuelve al balanceo
```

## 6. Parar todo y comprobar que se conserva el contenido

```bash
python3 auto-p2.py stop             # apaga todas las VMs sin borrar discos
python3 auto-p2.py monitor          # todas "shut off"
python3 auto-p2.py start            # vuelven a arrancar con sus datos
```

## 7. Liberar todo

```bash
python3 auto-p2.py undefine

sudo virsh list --all               # sin VMs del escenario
sudo ovs-vsctl list-br              # sin RED1, RED2 ni RED3
ls                                  # solo scripts, plantilla e imagen base
```

## 8. Pruebas automáticas (opcional)

No arrancan VMs ni tocan la red:

```bash
python3 -m unittest discover -s tests -v
```

## 9. Si algo falla

```bash
python3 auto-p2.py undefine         # limpia un escenario a medias y vuelve a empezar
sudo virsh list --all               # ver qué VMs existen
sudo virsh console s1               # consola de una VM (salir con Ctrl + ])
```

| Mensaje o síntoma | Solución |
| --- | --- |
| `Ya existe el escenario` | `python3 auto-p2.py undefine` y repite `define`. |
| `Faltan la imagen base o la plantilla XML` | Copia `cdps-vm-base-pc1.qcow2` y `plantilla-vm-pc1.xml` al directorio de trabajo. |
| `num_servers debe ser un entero de 1 a 5` | Corrige `auto-p2.json`. |
| `No hay terminal gráfico` | Ejecuta desde una sesión con entorno gráfico o instala `xterm`. |
| `curl` no responde o contesta un solo servidor | cloud-init no ha terminado: espera y repite el bucle del apartado 3. |
| `sudo` pide contraseña | El script no es interactivo: hace falta `sudo` sin contraseña. |
| `bash: $'\E[200~': orden no encontrada` o `cd: ...pc1~: No existe el fichero` | Es el pegado con marcadores (`^[[200~` al principio, `~` al final). Ejecuta una vez `bind 'set enable-bracketed-paste off'` (paso 0 del apartado 1) y pega de nuevo, un comando por línea. |

## 10. Mapa del código

| Orden | Qué hace | Dónde |
| --- | --- | --- |
| `define` | Bridges con `ovs-vsctl`, red del host, y por VM: qcow2 diferencial, cloud-init, ISO, XML y `virsh define` | `escenario/cmd_define.py`; `libvm/net.py`, `libvm/cloud_init.py`, `libvm/xml_vm.py` y `VM.define_vm()` en `lib_vm.py` |
| `start [vm]` | `virsh start` y consola de cada VM | `escenario/cmd_start.py`; `VM.start_vm()`; `libvm/console.py` |
| `stop [vm]` | `virsh shutdown` y espera al apagado | `escenario/cmd_stop.py`; `VM.stop_vm()` |
| `monitor` | `virsh domstate` y `ping` desde el host | `escenario/cmd_monitor.py` |
| `undefine` | Apaga, `virsh undefine`, borra ficheros, rutas, dirección del host y bridges | `escenario/cmd_undefine.py`; `escenario/host_net.py` |

La topología y las rutas salen de `escenario/topology.py`; Apache en los servidores y HAProxy en LB, de `escenario/services.py`. Todos los `.py` tienen 100 líneas o menos.
