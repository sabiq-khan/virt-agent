#!/usr/bin/env python3

import client
import subprocess

# TODO: Make the `cpu` and `memory` methods return more detailed information
 
def describe_cpu_cores():
    conn = client.connect()
    cpu_info = conn.getCPUMap()
    conn.close()

    available = 0
    for state in cpu_info[1]:
        if state == True:
            available += 1

    return available

def describe_disk_usage():
    df_output = subprocess.run(["df", "-h"], capture_output=True, text=True)
    grep_output = subprocess.run(["grep", "/$"], input=df_output.stdout, capture_output=True, text=True)
    disk_stats = grep_output.stdout.split()
    disk_usage = {"filesystem": disk_stats[0], "size": disk_stats[1], "used": disk_stats[2], "available": disk_stats[3], "usePercentage": disk_stats[4], "mountPoint": disk_stats[5]}

    return disk_usage
    
# Amount of free memory left on host in GB
def describe_memory_usage():
    conn = client.connect()
    memory = (conn.getFreeMemory()/1000000000)
    conn.close()

    return memory

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

    return {"freeCPU": cpu, "diskUsage": disk, "freeMemory": memory, "maxVCPU": max_vcpu}

def main():
    describe_host()

if __name__ == "__main__":
    main()
