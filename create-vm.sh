#!/bin/bash

set -o pipefail
set -o errtrace

log(){
    echo "[$(date -Iseconds)][${0}] ${1}"
}

cleanup(){
    # Terminates preseed server if it is still running
    if [[ -n $(docker ps -a | tail +2 | awk '{print $2}' | grep ^preseed-server$ || echo "") ]]; then
        log "Stopping preseed server..."
        docker rm -f preseed-server > /dev/null

        log "Preseed server stopped."
    fi
}

catch(){
    cleanup
    log "ERROR: An error occurred on line ${1}" 1>&2
    exit 1
}

help(){
cat <<EOF
    
USAGE: ./create-vm.sh [OPTIONS] [--file FILE]

Creates a Debian VM with the parameters provided via options or YAML file.

ARGUMENTS:

-h, --help, [none]      Prints this help message

--connection            A connection string specifying the libvirtd instance to connect to. 
                        To connect to a local instance of libvirtd, use 'qemu:///system'
                        To connect to libvirtd listening on a TCP socket on another machine, use 'qemu+tcp://domain-name/system'

--vm-name               The desired name for the VM, by which it will be identified in the libvirt back end

--cpu                   The number of vCPUs desired for the VM

--memory                The amount of memory in MiB desired for the VM

--disk-size             The amount of virtual disk space in GB desired for the VM

--network               The networking configuration for the VM
                        To make the VM reachable only by other VMs on the same host, use 'network=default'
                        To make the VM reachable over the LAN, use 'bridge=<bridge-interface-name>'

--os-version            The Debian version to install on the VM, e.g. 'debian12'

--disk-image            The location of the installation medium
                        Specify a file path to a local '.iso' file, e.g. /var/lib/libvirt/images/debian-12.4.0-amd64-netinst.iso
                        OR, specify the URL of a Debian installer, e.g. https://deb.debian.org/debian/dists/bookworm/main/installer-amd64/

--host-name             The host name of the VM, by which it is identified on its own OS

--domain-name           The domain name of the VM, by which it is identified to other devices on its network

--full-name             The full name of the Linux user being created during the Debian installation
                        Does not have to be an actual name, e.g. 'debian-user'

--username              The username of the Linux user being created during the Debian installation, e.g. 'debian-user'

-f, --file              A YAML file containing values for the above parameters

# Example YAML file

# Host settings
host:
  connection: qemu:///system # Points to local libvirtd
  #connection: qemu+tcp://localhost/system # Points to remote libvirtd on specified host

# VM settings
vm:
  name: debian           # VM name
  cpu: 2                 # CPU allocation in vCPUs
  memory: 2048           # Memory allocation in MiB
  diskSize: 20           # Virtual disk size in GB
  network: default       # 'default' uses libvirt NAT network, otherwise specify name of bridge
  #network: bridge=br0   # Enables bridge networking, bridge must already exist in advance

# OS settings
os:
  version: debian12      # OS version
  diskImage: /var/lib/libvirt/images/debian-12.4.0-amd64-netinst.iso  # Path to disk image
  #diskImage: https://deb.debian.org/debian/dists/bookworm/main/installer-amd64/ # Link to disk image root directory
  hostName: debian       # VM host name
  domainName: debian     # VM domain name

# User settings
user:
  fullName: debian-user  # Linux user full name (does not have to be a real name)
  userName: debian-user  # Linux username

EOF
}

# Creates a preseed file based on 'preseed-template.cfg'
create_preseed(){
    log "Creating Debian preseed..."
    cat preseed-template.cfg | sed -e "s|\$HOST_NAME|${host_name}|g" -e "s|\$DOMAIN_NAME|${domain_name}|g" -e "s|\$FULL_NAME|${full_name}|g" -e "s|\$USERNAME|${username}|g" -e "s|\$PASSWORD|${password}|g" > preseed.cfg

    log "'preseed.cfg' created!"
}

# Creates a web server that serves preseed on port 8080
serve_preseed(){
    log "Creating preseed server to allow remote access to '${preseed}'..."
    docker build . -f ./preseed.Dockerfile -t preseed-server

    log "Starting preseed server on port 8080..."
    docker run -d -p 8080:80 --name preseed-server preseed-server

    log "Preseed server started!"
}

create_vm(){
    log "Creating Debian user password..."
    local password=$(pwgen -1)

    create_preseed
    local preseed=preseed.cfg
    local initrd_inject="--initrd-inject ${preseed}"
    local extra_args="console=tty0 console=ttyS0,115200n8 serial"

    # For VM creation on a remote host
    if [[ -n $(echo $connection | grep ^qemu+tcp || echo "") ]]; then
        serve_preseed
        preseed=http://$(hostname --fqdn):8080/${preseed}
        initrd_inject=""
        extra_args="${extra_args} auto=true priority=critical preseed/url=${preseed} debian-installer/locale=en_US keyboard-configuration/xkb-keymap=us"
    fi

    log "Creating VM ${vm_name}..."
    virt-install \
    --connect $connection \
    --virt-type kvm \
    --name $vm_name  \
    --os-variant $os_version \
    --location $disk_image \
    --disk size=${disk_size} \
    --vcpus $cpu \
    --cpu host-passthrough \
    --ram $memory \
    --graphics none \
    --network $network \
    $initrd_inject \
    --extra-args "${extra_args}" \
    --noreboot

    log "Checking state of VM ${vm_name}..."
    virsh dominfo $vm_name
    if [[ $? -eq 1 ]]; then
        catch "${LINENO}: Creation of VM $vm_name failed."
    fi

    log "VM $vm_name successfully created!"
    log "VM name: ${vm_name}"
    log "VM host name: ${host_name}"
    log "VM domain name: ${domain_name}"
    log "Debian username: ${username}"
    log "Debian password: ${password}"
    log "Use virsh or virt-manager for more information."
}

main(){
    if [[ $# -eq 0 ]]; then
        help
        exit  
    fi

    while [[ $# -gt 0 ]]; do
        case $1 in
            -h | --help)
                help
                exit
                ;;
            --connection)
                local connection=${2}
                shift 2
                ;;
            --vm-name)
                local vm_name=${2}
                shift 2
                ;;
            --cpu)
                local cpu=${2}
                shift 2
                ;;
            --memory)
                local memory=${2}
                shift 2
                ;;
            --disk-size)
                local disk_size=${2}
                shift 2
                ;;
            --network)
                local network=${2}
                shift 2
                ;;
            --os-version)
                local os_version=${2}
                shift 2
                ;;
            --disk-image)
                local disk_image=${2}
                shift 2
                ;;
            --host-name)
                local host_name=${2}
                shift 2
                ;;
            --domain-name)
                local domain_name=${2}
                shift 2
                ;;
            --full-name)
                local full_name=${2}
                shift 2
                ;;
            --username)
                local username=${2}
                shift 2
                ;;
            -f | --file)
                if ! [[ -f $2 ]]; then
                    catch "${LINENO}: File '${2}' not found.$(help)"
                fi

                log "Parsing '${2}'..."
                # CLI options take precedence over YAML values
                # YAML value read only if no value was passed from CLI option
                # Host settings
                [[ -n $connection ]] || connection=$(cat $2 | yq -r .host.connection)
                # VM settings
                [[ -n $vm_name ]] || vm_name=$(cat $2 | yq -r .vm.name)
                [[ -n $cpu ]] || cpu=$(cat $2 | yq -r .vm.cpu)
                [[ -n $memory ]] || memory=$(cat $2 | yq -r .vm.memory)
                [[ -n $disk_size ]] || disk_size=$(cat $2 | yq -r .vm.diskSize)
                [[ -n $network ]] || network=$(cat $2 | yq -r .vm.network)
                # OS settings
                [[ -n $os_version ]] || os_version=$(cat $2 | yq -r .os.version)
                [[ -n $disk_image ]] || disk_image=$(cat $2 | yq -r .os.diskImage)
                [[ -n $host_name ]] || host_name=$(cat $2 | yq -r .os.hostName)
                [[ -n $domain_name ]] || domain_name=$(cat $2 | yq -r .os.domainName)
                # User settings
                [[ -n $full_name ]] || full_name=$(cat $2 | yq -r .user.fullName)
                [[ -n $username ]] || username=$(cat $2 | yq -r .user.userName)

                shift 2
                ;;
            *)
                catch "${LINENO}: '${1}' is not a valid option.$(help)"
        esac
    done

    if [[ -z $connection ]] || [[ -z $vm_name ]] || [[ -z $cpu ]] || [[ -z $memory ]] || [[ -z $disk_size ]] || [[ -z $network ]] || [[ -z $os_version ]] || [[ -z $disk_image ]] || [[ -z $host_name ]] || [[ -z $domain_name ]] || [[ -z $full_name ]] || [[ -z $username ]]; then
        catch "${LINENO}: Value not set."
    fi

    create_vm
    cleanup
}

# =============================================================================
# ENTRYPOINT
# =============================================================================
trap 'catch ${LINENO}.' ERR
main $@
