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

    createvm_cmd = subprocess.run(command, shell=False, capture_output=True)
    
    print(createvm_cmd.stdout)

    if (createvm_cmd.returncode != 0):
        raise ChildProcessError(createvm_cmd.stderr)

    tail_cmd = subprocess.run(["tail", "-n", "6"], input=createvm_cmd.stdout, shell=False, check=True, capture_output=True)
    
    return tail_cmd.stdout
    
def main():
    create_guest()

if __name__ == "__main__":
    main()

