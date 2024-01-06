#!/usr/bin/env python3

import client
import subprocess

# TODO: Make the `cpu` and `memory` methods return more detailed information
 
# Total and available number of CPU cores
def describe_cpu_cores():
    conn = client.connect()
    cpu_info = conn.getCPUMap()
    conn.close()

    available = 0
    for state in cpu_info[1]:
        if state == True:
            available += 1

    return {"total": cpu_info[0], "available": available}

# Total and remaining disk space in volume
def describe_disk_usage():
    df_output = subprocess.run(["df", "-h"], shell=False, check=True, capture_output=True, text=True)
    grep_output = subprocess.run(["grep", "/$"], input=df_output.stdout, shell=False, check=True, capture_output=True, text=True)
    disk_stats = grep_output.stdout.split()
    disk_usage = {"filesystem": disk_stats[0], "size": disk_stats[1], "used": disk_stats[2], "available": disk_stats[3], "usePercentage": disk_stats[4], "mountPoint": disk_stats[5]}

    return disk_usage
    
# Memory usage on host in KiB
def describe_memory_usage():
    free_output = subprocess.run(["free"], shell=False, check=True, capture_output=True, text=True)
    head_output = subprocess.run(["head", "-n", "2"], input=free_output.stdout, shell=False, check=True, capture_output=True, text=True)
    print(head_output.stdout)

    memory_data = head_output.stdout.split("\n")
    memory_usage = {}
    keys = memory_data[0].split()
    values = memory_data[1].split()[1:]

    for key, value in zip(keys, values):
        memory_usage[key] = f"{value}Ki"

    return memory_usage

# Max vCPUs per VM on host
def get_max_vcpu():
    conn = client.connect()
    max_vcpu = conn.getMaxVcpus(None)
    conn.close()

    return max_vcpu

def describe_host():
    cpu = describe_cpu_cores()
    disk = describe_disk_usage()
    memory = describe_memory_usage()
    max_vcpu = get_max_vcpu()

    return {"cpu": cpu, "disk": disk, "memory": memory, "maxVCPU": max_vcpu}

def main():
    #describe_host()
    print(describe_memory_usage())

if __name__ == "__main__":
    main()
