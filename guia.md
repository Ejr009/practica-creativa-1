# Guía de instalación y prueba

Pasos para desplegar el escenario en el laboratorio y comprobar que todo funciona. Cada paso indica qué ejecutar y qué resultado esperar.

## 1. Requisitos

En el servidor del laboratorio (UDS) deben estar disponibles: `python3`, `virsh` (libvirt/KVM), `ovs-vsctl` (Open vSwitch), `qemu-img`, `genisoimage`, `sudo` sin contraseña y un terminal gráfico (`gnome-terminal`, `xfce4-terminal` o `xterm`) para las consolas.

## 2. Preparación

```bash
/lab/cnvr/bin/prepare-vnx-debian          # una vez por sesión de laboratorio

mkdir -p ~/pc1 && cd ~/pc1
git clone https://github.com/Ejr009/practica-creativa-1 .
cp /lab/cdps/pc1/cdps-vm-base-pc1.qcow2 .  # imagen base (no se incluye en Git)
ls                                          # debe haber: auto-p2.py lib_vm.py auto-p2.json plantilla-vm-pc1.xml cdps-vm-base-pc1.qcow2
```

La imagen base también está en <https://idefix.dit.upm.es/download/cdps/pc1/>. El script no copia ficheros: la imagen y la plantilla deben estar ya en el directorio de trabajo.

## 3. Configuración

Edita `auto-p2.json`:

```json
{
  "num_servers": 3,
  "debug": false
}
```

`num_servers` admite de 1 a 5. Con `"debug": true` se muestran los comandos que ejecuta el script.

## 4. Paso a paso

### 4.1 Definir el escenario

```bash
python3 auto-p2.py define
```

Comprobación:

```bash
sudo ovs-vsctl list-br      # RED1, RED2, RED3
sudo virsh list --all       # c1, fw, lb, s1..sN en estado "shut off"
ls                          # un .qcow2, un .xml y un -cdata.iso por VM
```

### 4.2 Arrancar

```bash
python3 auto-p2.py start
```

Se abre una consola por VM. cloud-init tarda unos minutos en terminar la primera vez (hostname, red, Apache/HAProxy). Si quieres entrar en una VM, usa las credenciales de la imagen del laboratorio (las de la práctica 2) y comprueba con `cloud-init status` (debe decir `done`).

### 4.3 Monitorizar

```bash
python3 auto-p2.py monitor
watch -n2 python3 auto-p2.py monitor     # refresco continuo
```

Salida esperada cuando todo está arriba:

```text
VM   ESTADO     IP            PING
c1   running    10.0.10.2     ok
fw   running    10.0.10.1     ok
lb   running    10.0.10.130   ok
s1   running    10.0.10.66    ok
```

Mientras cloud-init no termine, el ping puede aparecer como `sin respuesta`.

### 4.4 Probar conectividad entre redes

Desde el host (que tiene `10.0.10.3` en RED1 y rutas hacia RED2 y RED3 a través de FW):

```bash
ping -c1 10.0.10.2      # C1 (RED1)
ping -c1 10.0.10.1      # FW
ping -c1 10.0.10.130    # LB por RED2
ping -c1 10.0.10.65     # LB por RED3
ping -c1 10.0.10.66     # S1
```

Desde una consola de C1 también debes alcanzar `10.0.10.66` (a través de FW y LB), y viceversa.

### 4.5 Probar el balanceo (HAProxy + Apache)

```bash
for i in 1 2 3 4 5 6; do curl -s http://10.0.10.130/; done
```

Debe alternar `<h1>Servidor s1</h1>`, `<h1>Servidor s2</h1>`, etc., una por servidor definido.

### 4.6 Interfaz de gestión de HAProxy

- Web: abre `http://10.0.10.130:8404/stats` desde el host. Muestra el estado de cada servidor y permite activarlos o desactivarlos.
- En texto: `curl -s "http://10.0.10.130:8404/stats;csv" | cut -d, -f1,2,18`
- API en tiempo de ejecución, desde una consola de LB (si `socat` está instalado):

```bash
echo "show servers state" | sudo socat stdio /run/haproxy/admin.sock
```

### 4.7 Parar y arrancar una sola VM

```bash
python3 auto-p2.py stop s1
sleep 10
for i in 1 2 3 4; do curl -s http://10.0.10.130/; done    # ya no responde s1
python3 auto-p2.py monitor                                # s1 aparece "shut off"
python3 auto-p2.py start s1                               # vuelve al balanceo cuando arranca
```

### 4.8 Parar todo y comprobar persistencia

```bash
python3 auto-p2.py stop       # apagado ordenado, los discos se conservan
python3 auto-p2.py start      # vuelven con sus cambios
```

### 4.9 Liberar el escenario

```bash
python3 auto-p2.py undefine
sudo virsh list --all          # sin VMs del escenario
sudo ovs-vsctl list-br         # sin RED1, RED2, RED3
ls                             # solo quedan los scripts, la plantilla y la imagen base
```

## 5. Pruebas automáticas

No arrancan VMs ni tocan la red del host:

```bash
python3 -m unittest discover -s tests -v
```

## 6. Problemas frecuentes

| Síntoma | Causa y solución |
| --- | --- |
| `Ya existe el escenario` | Hay un escenario definido: ejecuta `python3 auto-p2.py undefine` y vuelve a empezar. |
| `Faltan la imagen base o la plantilla XML` | Copia `cdps-vm-base-pc1.qcow2` y `plantilla-vm-pc1.xml` al directorio de trabajo. |
| `num_servers debe ser un entero de 1 a 5` | Corrige `auto-p2.json`. |
| `No hay terminal gráfico` | Ejecuta el script desde una sesión con entorno gráfico o instala `xterm`. |
| `curl` no responde o solo contesta un servidor | cloud-init aún no ha terminado en LB o en los servidores; espera y repite. Revisa `cloud-init status` y `/var/log/cloud-init-output.log`. |
| `sudo` pide contraseña | El script no es interactivo: el usuario debe tener `sudo` sin contraseña en el laboratorio. |
| Quedan restos tras un fallo | Ejecuta `python3 auto-p2.py undefine`; usa el estado guardado en `.auto-p2-state.json`. |

## 7. Cómo funciona por dentro

| Orden | Qué hace | Dónde |
| --- | --- | --- |
| `define` | Crea los bridges con `ovs-vsctl`, configura el host, y para cada VM crea el qcow2 diferencial, los ficheros cloud-init y su ISO, el XML y hace `virsh define` | `define()` en `auto-p2.py`; `NET.create_net()` y `VM.define_vm()` en `lib_vm.py` |
| `start [vm]` | `virsh start` y abre la consola de cada VM | `start()`; `VM.start_vm()`, `VM.show_console_vm()` |
| `stop [vm]` | `virsh shutdown` y espera al apagado | `stop()`; `VM.stop_vm()` |
| `monitor` | Estado con `virsh domstate` y `ping` desde el host | `monitor()` |
| `undefine` | Apaga, `virsh undefine`, borra ficheros, rutas, dirección del host y bridges | `undefine()` |

La topología y las rutas salen de `specifications()`. Los ficheros extra de cloud-init (Apache en los servidores, HAProxy en LB) salen de `services()`.
