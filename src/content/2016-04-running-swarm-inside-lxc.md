Title: Running Docker Swarm inside LXC
Date: 2016-04-13 18:00
Author: andreacorbellini
Category: information-technology
Tags: docker, swarm, lxc, containers, distributed-computing
Slug: docker-swarm-inside-lxc
Status: published

I've been using [Docker Swarm](https://docs.docker.com/swarm/) inside [LXC](https://linuxcontainers.org/lxc/introduction/) containers for a while now, and I thought that I could share my experience with you. Due to their nature, LXC containers are pretty lightweight and require very few resources if compared to virtual machines. This makes LXC ideal for development and simulation purposes. Running Docker Swarm inside LXC requires a few steps that I'm going to show you in this tutorial.

Before we begin, a quick premise: LXC, Docker and Swarm can be configured in many different ways. Here I'm showing just my preferred setup: LXC with AppArmor disabled, Docker with the OverlayFS storage driver, Swarm with etcd discovery. There exist many other kind of configurations that can work under LXC &mdash; leave a comment if you want to know more.

**Overview:**

1. [Create the Swarm Manager container](#step-1)
1. [Modify configuration for the Swarm Manager container](#step-2)
1. [Load the OverlayFS module](#step-3)
1. [Start the container and install Docker](#step-4)
1. [Check if Docker is working](#step-5)
1. [Set up the Swarm Manager](#step-6)
1. [Create the Swarm Agents](#step-7)
1. [Play with the Swarm](#step-8)

**Terminology:**

* the *host* is the system that will create and start the LXC containers (e.g. your laptop);
* the *manager* is the LXC container that will run the Swarm manager (it'll run the `swarm manage` command);
* an *agent* is one of the many LXC containers that will run a Swarm agent node (it'll run the `swarm join` command);

To avoid ambiguity, all commands will be prefixed with a prompt such as `root@host:~#`, `root@swarm-manager:~#` and `root@swarm-agent-1:~#`.

**Prerequisites:**

This tutorial assumes that you have at least a vague idea of what Docker and Docker Swarm are. You should also be familiar with the shell.

This tutorial has been succesfully tested on Ubuntu 15.10 (that ships with Docker 1.6) and Ubuntu 16.04 LTS (Docker 1.10), but it may work on other distributions and Docker versions as well.

## Step 1: Create the Swarm Manager container {#step-1}

Create a new LXC container with:

    :::console
    root@host:~# lxc-create -t download -n swarm-manager

When prompted, choose your favorite distribution and architecture. I chose `ubuntu` / `xenial` / `amd64`.

`lxc-create` needs to run as root, [unprivileged containers](https://www.stgraber.org/2014/01/17/lxc-1-0-unprivileged-containers/) won't work. We could actually make Docker start inside an unprivileged container, the problem is that we wouldn't be allowed to create block and character devices, and many Docker containers need this ability.

## Step 2: Modify the configuration for the Swarm Manager container {#step-2}

Before starting the LXC container, open the file `/var/lib/lxc/swarm-manager/config` on the host and add the following configuration to the bottom of the file:

    :::bash
    # Distribution configuration
    # ...

    # Container specific configuration
    # ...

    # Network configuration
    # ...

    # Allow running Docker inside LXC
    lxc.aa_profile = unconfined
    lxc.cap.drop =

The first rule (`lxc.aa_profile = unconfined`) disables AppArmor confinement. The second one (`lxc.cap.drop =`) gives all capabilities to the processes in LXC container.

These two rules may seem harmful from a security standpoint, and in fact they are. However we must remember that we will be running Docker inside the LXC container. Docker already ships with its own AppArmor profile and the two rules above are needed exactly for the purposes of letting Docker talk to AppArmor.

So, while Docker itself won't be confined, **Docker containers will be confined**, and this is an encouraging fact.

## Step 3: Load the OverlayFS module {#step-3}

OverlayFS is shipped with Ubuntu, but not enabled by default. To enable it:

    :::console
    root@host:~# modprobe overlay

It is important to do this step before installing Docker. Docker supports various storage drivers and when Docker is installed for the first time it tries to detect the most appropriate one for the system. If Docker detects that OverlayFS is not loaded, it'll fall back to the device mapper. There's nothing wrong with the device mapper, we can make it work, however, as I said at the beginning, in this tutorial I'm focusing only on OverlayFS.

If you want to load OverlayFS at boot, instead of doing it manually after every reboot, add it to `/etc/modules-load.d/modules.conf`:

    :::console
    root@host:~# echo overlay >> /etc/modules-load.d/modules.conf

## Step 4: Start the container and install Docker {#step-4}

It's time to see if we did everything right!

    :::console
    root@host:~# lxc-start -n swarm-manager
    root@host:~# lxc-attach -n swarm-manager
    root@swarm-manager:~# apt update
    root@swarm-manager:~# apt install docker.io

Installation should complete without any problem. If you get an error like this:

    Job for docker.service failed because the control process exited with error code. See "systemctl status docker.service" and "journalctl -xe" for details.
    invoke-rc.d: initscript docker, action "start" failed.
    dpkg: error processing package docker.io (--configure):
     subprocess installed post-installation script returned error exit status 1

It means that Docker failed to start. Try checking `systemctl status docker` as suggested, or run `docker daemon` manually. You might get an error like this:

    :::console
    root@swarm-manager:~# docker daemon
    WARN[0000] devmapper: Udev sync is not supported. This will lead to unexpected behavior, data loss and errors. For more information, see https://docs.docker.com/reference/commandline/daemon/#daemon-storage-driver-option
    ERRO[0000] There are no more loopback devices available.
    ERRO[0000] [graphdriver] prior storage driver "devicemapper" failed: loopback attach failed
    FATA[0000] Error starting daemon: error initializing graphdriver: loopback attach failed

In this case, Docker is using the devicemapper storage driver and is complaining about the lack of loopback devices. If that's the case, check whether OverlayFS is loaded and reinstall Docker.

Or you might get an error like this:

    :::console
    root@swarm-manager:~# docker daemon
    XXX

It this other case, Docker is complaining about the fact that it can't talk to AppArmor. Check the configuration for the LXC container.

## Step 5: Check if Docker is working {#step-5}

Once you are all set, you should be able to use Docker: try running `docker info`, `docker ps` or launch a container:

    :::console
    root@swarm-manager:~# docker run --rm docker/whalesay cowsay burp!
    Unable to find image 'docker/whalesay:latest' locally
    latest: Pulling from docker/whalesay
    ...
    Status: Downloaded newer image for docker/whalesay:latest
     _______
    < burp! >
     -------
        \
         \
          \
                        ##        .
                  ## ## ##       ==
               ## ## ## ##      ===
           /""""""""""""""""___/ ===
      ~~~ {~~ ~~~~ ~~~ ~~~~ ~~ ~ /  ===- ~~~
           \______ o          __/
            \    \        __/
              \____\______/

It appears to be working. By the way, we can check whether Docker is correctly confining containers. Try running a Docker container and check on the host the output of `aa-status`: you should see a process running with the `docker-default` profile. For example:

    :::console
    root@swarm-manager:~# docker run --rm ubuntu bash -c 'while true; do sleep 1; echo -n zZ; done'
    zZzZzZzZzZzZzZzZ...

    # On another shell
    root@host:~# aa-status
    apparmor module is loaded.
    5 profiles are loaded.
    5 profiles are in enforce mode.
       /sbin/dhclient
       /usr/lib/NetworkManager/nm-dhcp-client.action
       /usr/lib/NetworkManager/nm-dhcp-helper
       /usr/lib/connman/scripts/dhclient-script
       docker-default
    0 profiles are in complain mode.
    4 processes have profiles defined.
    4 processes are in enforce mode.
       /sbin/dhclient (797)
       /sbin/dhclient (2832)
       docker-default (6956)
       docker-default (6973)
    0 processes are in complain mode.
    0 processes are unconfined but have a profile defined.

    root@host:~# ps -ef | grep 6956
    root      6956  4982  0 17:17 ?        00:00:00 bash -c while true; do sleep 1; echo -n zZ; done
    root      6973  6956  0 17:17 ?        00:00:00 sleep 1
    root      6982  6808  0 17:17 pts/3    00:00:00 grep --color=auto 6956

Yay! Everything is running as expected: we launched a process inside a Docker container, and that process is running with the `docker-default` AppArmor profile. Once again: even if LXC is running unconfined, our Docker containers are not.

## Step 6: Set up the Swarm Manager {#step-6}

That was the hardest part. Now we can proceed setting up Swarm as we would usually do.

As I said at the beginning, Swarm can be configured in many ways. In this tutorial I'll show how to set it up with etcd discovery. First of all, we need the IP address of the LXC container:

    :::console
    root@swarm-manager:~# ifconfig eth0
    eth0      Link encap:Ethernet  HWaddr 00:16:3e:8e:cb:43
              inet addr:10.0.3.154  Bcast:10.0.3.255  Mask:255.255.255.0
              inet6 addr: fe80::216:3eff:fe8e:cb43/64 Scope:Link
              UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1
              RX packets:23177 errors:0 dropped:0 overruns:0 frame:0
              TX packets:20859 errors:0 dropped:0 overruns:0 carrier:0
              collisions:0 txqueuelen:1000
              RX bytes:147652946 (147.6 MB)  TX bytes:1455613 (1.4 MB)

`10.0.3.154` is my IP address. Let's start etcd:

    :::console
    root@swarm-manager:~# SWARM_MANAGER_IP=10.0.3.154

    root@swarm-manager:~# docker run -d --restart=always --name=etcd -p 4001:4001 -p 2380:2380 -p 2379:2379 \
                                quay.io/coreos/etcd -name etcd0 \
                                -advertise-client-urls http://$SWARM_MANAGER_IP:2379,http://$SWARM_MANAGER_IP:4001 \
                                -listen-client-urls http://0.0.0.0:2379,http://0.0.0.0:4001 \
                                -initial-advertise-peer-urls http://$SWARM_MANAGER_IP:2380 \
                                -listen-peer-urls http://0.0.0.0:2380 \
                                -initial-cluster-token etcd-cluster-1 \
                                -initial-cluster etcd0=http://$SWARM_MANAGER_IP:2380 \
                                -initial-cluster-state new
    Unable to find image 'quay.io/coreos/etcd:latest' locally
    latest: Pulling from coreos/etcd
    ...
    Status: Downloaded newer image for quay.io/coreos/etcd:latest
    e742278a97d2ad3f88658aa871903d20b4094e551969a03aa8332d3876fe5d0d

    root@swarm-manager:~# docker ps
    CONTAINER ID        IMAGE                 COMMAND                  CREATED             STATUS              PORTS                                                                NAMES
    e742278a97d2        quay.io/coreos/etcd   "/etcd -name etcd0 -a"   32 seconds ago      Up 31 seconds       0.0.0.0:2379-2380->2379-2380/tcp, 0.0.0.0:4001->4001/tcp, 7001/tcp   etcd

Replace `10.0.3.154` with the IP address of your LXC container.

Note that I've started etcd with `--restart=always`, so that every time etcd is automatically started when the LXC container starts. With this option, etcd will restart even if you explicitly stop it. Drop `--restart=always` if that's not what you want.

Now we can start the Swarm manager:

    :::console
    root@swarm-manager:~# docker run -d --restart=always --name=swarm -p 3375:3375 \
                                swarm manage -H 0.0.0.0:3375 etcd://$SWARM_MANAGER_IP:2379
    Unable to find image 'swarm:latest' locally
    latest: Pulling from library/swarm
    ...
    Status: Downloaded newer image for swarm:latest
    8080c93c544ff92cc2cf682ff0bbc82e0d2dfb01e1f98f202c3a0801d3427330

    root@swarm-manager:~# docker ps
    CONTAINER ID        IMAGE                 COMMAND                  CREATED             STATUS              PORTS                                                                NAMES
    46b556e73e87        swarm                 "/swarm manage -H 0.0"   3 seconds ago       Up 2 seconds        2375/tcp, 0.0.0.0:3375->3375/tcp                                     swarm
    e742278a97d2        quay.io/coreos/etcd   "/etcd -name etcd0 -a"   7 minutes ago       Up 7 minutes        0.0.0.0:2379-2380->2379-2380/tcp, 0.0.0.0:4001->4001/tcp, 7001/tcp   etcd

Our Swarm manager is up and running. We can connect to it and issue a few commands:

    :::console
    root@swarm-manager:~# docker -H localhost:3375 info
    Containers: 0
     Running: 0
     Paused: 0
     Stopped: 0
    Images: 0
    Server Version: swarm/1.1.3
    Role: primary
    Strategy: spread
    Filters: health, port, dependency, affinity, constraint
    Nodes: 0
    Plugins:
     Volume:
     Network:
    Kernel Version: 4.4.0-15-generic
    Operating System: linux
    Architecture: amd64
    CPUs: 0
    Total Memory: 0 B
    Name: d39c33295ef3

As you can see there are no nodes connected, as we would expect. Everything looks good.

## Step 7: Create the Swarm Agents {#step-7}

Our Swarm manager can't do anything interesting without agent nodes. Creating new LXC containers for the agents is not much different from what we already did with the manager. To set up new agents in an automatic fashion I've created a script, so that you don't need to repeat the steps manually:

    #!/bin/bash

    set -eu

    SWARM_MANAGER_IP=10.0.3.154
    DOWNLOAD_DIST=ubuntu
    DOWNLOAD_RELEASE=xenial
    DOWNLOAD_ARCH=amd64

    for LXC_NAME in "$@"
    do
        LXC_PATH="/var/lib/lxc/$LXC_NAME"
        LXC_ROOTFS="$LXC_PATH/rootfs"

        # Create the container.
        lxc-create -t download -n "$LXC_NAME" -- \
            -d "$DOWNLOAD_DIST" -r "$DOWNLOAD_RELEASE" -a "$DOWNLOAD_ARCH"

        cat <<EOF >> "$LXC_PATH/config"
    # Allow running Docker inside LXC
    lxc.aa_profile = unconfined
    lxc.cap.drop =
    EOF

        # Start the container and wait for networking to start.
        lxc-start -n "$LXC_NAME"
        sleep 10s

        # Install Docker.
        lxc-attach -n "$LXC_NAME" -- apt-get update
        lxc-attach -n "$LXC_NAME" -- apt-get install -y docker.io

        # Tell Docker to listen on all interfaces.
        sed -i -e 's/^#DOCKER_OPTS=.*$/DOCKER_OPTS="-H 0.0.0.0:2375"/' "$LXC_ROOTFS/etc/default/docker"
        lxc-attach -n "$LXC_NAME" -- systemctl restart docker

        # Join the Swarm.
        SWARM_AGENT_IP="$(lxc-attach -n "$LXC_NAME" -- ifconfig eth0 | grep -Po '(?<=inet addr:)\S+')"
        lxc-attach -n "$LXC_NAME" -- docker run -d --restart=always --name=swarm \
            swarm join --addr="$SWARM_AGENT_IP:2375" "etcd://$SWARM_MANAGER_IP:2379"
    done

Be sure to change the values for `SWARM_MANAGER_IP`, `DOWNLOAD_DIST`, `DOWNLOAD_RELEASE` and `DOWNLOAD_ARCH` to fit your needs.

Thanks to this script, creating 10 new agents is as simple as running one command:

    :::console
    root@host:~# ./swarm-agent-create swarm-agent-{0..9}

Here's an explaination of what the script does:

* It first sets up a new LXC container following steps 1-5 above, that is: create a new LXC container (with `lxc-create`), apply the LXC configuration (`lxc.aa_profile` and `lxc.cap.drop` rules), start the container and install Docker.

        :::bash
        LXC_PATH="/var/lib/lxc/$LXC_NAME"
        LXC_ROOTFS="$LXC_PATH/rootfs"

        # Create the container.
        lxc-create -t download -n "$LXC_NAME" -- \
            -d "$DOWNLOAD_DIST" -r "$DOWNLOAD_RELEASE" -a "$DOWNLOAD_ARCH"

        cat <<EOF >> "$LXC_PATH/config"
        # Allow running Docker inside LXC
        lxc.aa_profile = unconfined
        lxc.cap.drop =
        EOF

        # Start the container and wait for networking to start.
        lxc-start -n "$LXC_NAME"
        sleep 10s

        # Install Docker.
        lxc-attach -n "$LXC_NAME" -- apt-get update
        lxc-attach -n "$LXC_NAME" -- apt-get install -y docker.io

* Our Swarm agents need to be reachable by the manager. For this reason we need to configure them so that they bind to a public interface. To do so, the script adds `DOCKER_OPTS="-H 0.0.0.0:2375"` and restarts Docker.

        :::bash
        # Tell Docker to listen on all interfaces.
        sed -i -e 's/^#DOCKER_OPTS=.*$/DOCKER_OPTS="-H 0.0.0.0:2375"/' "$LXC_ROOTFS/etc/default/docker"
        lxc-attach -n "$LXC_NAME" -- systemctl restart docker

* Lastly, the script checks the IP address for the LXC container and it launches Swarm.

        :::bash
        # Join the Swarm.
        SWARM_AGENT_IP="$(lxc-attach -n "$LXC_NAME" -- ifconfig eth0 | grep -Po '(?<=inet addr:)\S+')"
        lxc-attach -n "$LXC_NAME" -- docker run -d --restart=always --name=swarm \
            swarm join --addr="$SWARM_AGENT_IP:2375" "etcd://$SWARM_MANAGER_IP:2379"

## Step 8: Play with the Swarm {#step-8}

Now, if we check `docker info` on the Swarm manager, we should see 10 healthy nodes:

    :::console
    root@swarm-manager:~# docker -H localhost:3375 info
    Containers: 10
     Running: 10
     Paused: 0
     Stopped: 0
    Images: 10
    Server Version: swarm/1.1.3
    Role: primary
    Strategy: spread
    Filters: health, port, dependency, affinity, constraint
    Nodes: 10
     swarm-agent-0: 10.0.3.73:2375
      └ Status: Healthy
      └ Containers: 1
      └ Reserved CPUs: 0 / 4
      └ Reserved Memory: 0 B / 4.052 GiB
      └ Labels: executiondriver=native-0.2, kernelversion=4.4.0-15-generic, operatingsystem=Ubuntu 16.04, storagedriver=overlay
      └ Error: (none)
      └ UpdatedAt: 2016-04-13T15:32:35Z
     swarm-agent-1: 10.0.3.97:2375
      └ Status: Healthy
      └ Containers: 1
      └ Reserved CPUs: 0 / 4
      └ Reserved Memory: 0 B / 4.052 GiB
      └ Labels: executiondriver=native-0.2, kernelversion=4.4.0-15-generic, operatingsystem=Ubuntu 16.04, storagedriver=overlay
      └ Error: (none)
      └ UpdatedAt: 2016-04-13T15:31:49Z
     swarm-agent-2: 10.0.3.58:2375
      └ Status: Healthy
      └ Containers: 1
      └ Reserved CPUs: 0 / 4
      └ Reserved Memory: 0 B / 4.052 GiB
      └ Labels: executiondriver=native-0.2, kernelversion=4.4.0-15-generic, operatingsystem=Ubuntu 16.04, storagedriver=overlay
      └ Error: (none)
      └ UpdatedAt: 2016-04-13T15:31:54Z
     swarm-agent-3: 10.0.3.195:2375
      └ Status: Healthy
      └ Containers: 1
      └ Reserved CPUs: 0 / 4
      └ Reserved Memory: 0 B / 4.052 GiB
      └ Labels: executiondriver=native-0.2, kernelversion=4.4.0-15-generic, operatingsystem=Ubuntu 16.04, storagedriver=overlay
      └ Error: (none)
      └ UpdatedAt: 2016-04-13T15:32:03Z
     swarm-agent-4: 10.0.3.235:2375
      └ Status: Healthy
      └ Containers: 1
      └ Reserved CPUs: 0 / 4
      └ Reserved Memory: 0 B / 4.052 GiB
      └ Labels: executiondriver=native-0.2, kernelversion=4.4.0-15-generic, operatingsystem=Ubuntu 16.04, storagedriver=overlay
      └ Error: (none)
      └ UpdatedAt: 2016-04-13T15:32:22Z
     swarm-agent-5: 10.0.3.174:2375
      └ Status: Healthy
      └ Containers: 1
      └ Reserved CPUs: 0 / 4
      └ Reserved Memory: 0 B / 4.052 GiB
      └ Labels: executiondriver=native-0.2, kernelversion=4.4.0-15-generic, operatingsystem=Ubuntu 16.04, storagedriver=overlay
      └ Error: (none)
      └ UpdatedAt: 2016-04-13T15:32:16Z
     swarm-agent-6: 10.0.3.222:2375
      └ Status: Healthy
      └ Containers: 1
      └ Reserved CPUs: 0 / 4
      └ Reserved Memory: 0 B / 4.052 GiB
      └ Labels: executiondriver=native-0.2, kernelversion=4.4.0-15-generic, operatingsystem=Ubuntu 16.04, storagedriver=overlay
      └ Error: (none)
      └ UpdatedAt: 2016-04-13T15:32:21Z
     swarm-agent-7: 10.0.3.140:2375
      └ Status: Healthy
      └ Containers: 1
      └ Reserved CPUs: 0 / 4
      └ Reserved Memory: 0 B / 4.052 GiB
      └ Labels: executiondriver=native-0.2, kernelversion=4.4.0-15-generic, operatingsystem=Ubuntu 16.04, storagedriver=overlay
      └ Error: (none)
      └ UpdatedAt: 2016-04-13T15:31:43Z
     swarm-agent-8: 10.0.3.95:2375
      └ Status: Healthy
      └ Containers: 1
      └ Reserved CPUs: 0 / 4
      └ Reserved Memory: 0 B / 4.052 GiB
      └ Labels: executiondriver=native-0.2, kernelversion=4.4.0-15-generic, operatingsystem=Ubuntu 16.04, storagedriver=overlay
      └ Error: (none)
      └ UpdatedAt: 2016-04-13T15:32:17Z
     swarm-agent-9: 10.0.3.125:2375
      └ Status: Healthy
      └ Containers: 1
      └ Reserved CPUs: 0 / 4
      └ Reserved Memory: 0 B / 4.052 GiB
      └ Labels: executiondriver=native-0.2, kernelversion=4.4.0-15-generic, operatingsystem=Ubuntu 16.04, storagedriver=overlay
      └ Error: (none)
      └ UpdatedAt: 2016-04-13T15:32:30Z
    Plugins:
     Volume:
     Network:
    Kernel Version: 4.4.0-15-generic
    Operating System: linux
    Architecture: amd64
    CPUs: 40
    Total Memory: 40.52 GiB
    Name: d39c33295ef3

Let's try running a command on the Swarm:

    :::console
    root@swarm-manager:~# docker -H localhost:3375 run -i --rm docker/whalesay cowsay 'It works!'
     ___________
    < It works! >
     -----------
        \
         \
          \
                        ##        .
                  ## ## ##       ==
               ## ## ## ##      ===
           /""""""""""""""""___/ ===
      ~~~ {~~ ~~~~ ~~~ ~~~~ ~~ ~ /  ===- ~~~
           \______ o          __/
            \    \        __/
              \____\______/

## Conclusion

We created a Swarm cluster consisting of one manager and 10 agents, and we kept memory and disk usage low thanks to LXC containers. We also succeeded in confining our Docker containers with AppArmor. Overall, this setup is probably not ideal for use in a production environment, but very useful for simulating clusters on your laptop.

I hope you enjoyed the tutorial. Feel free to leave a comment if you have questions!
