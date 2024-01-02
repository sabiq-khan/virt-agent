#!/usr/bin/env python3

import libvirt
import sys

def connect():
    try:
        conn = libvirt.openReadOnly(f"qemu:///system")
        return conn
    except libvirt.libvirtError:
        print("Failed to open connection to the hypervisor.", file=sys.stderr)
        sys.exit(1)
