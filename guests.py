#!/usr/bin/env python3

import libvirt
import sys
import subprocess

# TODO: Implement methods to describe, update, and delete guests

def create_guest(name="debian", cpu=2, memory=2048, disk_size=20, network="bridge=br0", os_version="debian12", disk_image="https://deb.debian.org/debian/dists/bookworm/main/installer-amd64/", host_name="debian", domain_name="debian.example.com", full_name="debian-user", username="debian-user"):
    command = [
        "./create-vm.sh",
        f"--connection qemu:///system",
        f"--vm-name {name}",
        f"--cpu {cpu}",
        f"--memory {memory}",
        f"--disk-size {disk_size}",
        f"--network {network}",
        f"--os-version {os_version}",
        f"--disk-image {disk_image}",
        f"--host-name {host_name}",
        f"--domain-name {domain_name}",
        f"--full-name {full_name}",
        f"--username {username}"
    ]

    subprocess.run(command, check=True)

def main():
    create_guest()

if __name__ == "__main__":
    main()

