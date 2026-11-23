#!/usr/bin/env python3
"""Creativa 1 de CDPS: define, start, stop, monitor y undefine del escenario KVM."""

import argparse
import logging
import sys

from escenario.cmd_define import define
from escenario.cmd_monitor import monitor
from escenario.cmd_start import start
from escenario.cmd_stop import stop
from escenario.cmd_undefine import undefine
from escenario.config import initialize_logging, read_config
from libvm.shell import ErrorEscenario


LOG = logging.getLogger("auto-p2")
ORDENES = ["define", "start", "stop", "undefine", "monitor"]


def parse_args():
    parser = argparse.ArgumentParser(description="CDPS Creativa 1: gestión de escenario KVM")
    parser.add_argument("orden", choices=ORDENES)
    parser.add_argument("vm", nargs="?", help="solo para start/stop: nombre de una VM (p.ej. s1)")
    args = parser.parse_args()
    if args.vm and args.orden not in ("start", "stop"):
        parser.error("el nombre de VM solo se admite con start y stop")
    return args


def load_config(orden):
    """Lee auto-p2.json. stop, undefine y monitor funcionan aunque esté roto:
    así se puede recuperar el laboratorio usando solo el estado guardado."""
    try:
        cfg = read_config()
    except ErrorEscenario as config_error:
        if orden not in ("stop", "undefine", "monitor"):
            raise
        initialize_logging(False)
        LOG.warning("Configuración inválida, se usa el estado para limpiar: %s", config_error)
        return None
    initialize_logging(cfg.get("debug", False))
    return cfg


def run(args, cfg):
    if args.orden == "define":
        define(cfg["num_servers"])
    elif args.orden == "start":
        start(args.vm)
    elif args.orden == "stop":
        stop(args.vm)
    elif args.orden == "monitor":
        monitor()
    else:
        undefine()


def main():
    args = parse_args()
    try:
        run(args, load_config(args.orden))
    except (ErrorEscenario, OSError) as exc:
        LOG.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
