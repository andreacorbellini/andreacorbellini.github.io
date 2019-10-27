Title: Are LXC and Docker secure?
Date: 2015-02-20 16:36
Author: andreacorbellini
Category: cloud
Tags: docker, lxc, security
Slug: are-lxc-and-docker-secure
Status: published

Since its initial release in 2008, LXC has become widespread among servers. Today, it is becoming the preferred deployment strategy in many contexts, also thanks to Docker and, more recently, LXD.

LXC and Docker are used not only to achieve modular architecture design, but also as a way to run untrusted code in an isolated environment.

We can agree that the LXC and Docker ecosystems are great and work well, but there's an important question that I believe everyone should ask, but too few people are asking: **are LXC and Docker secure?**

<figure>
  <img src="{static}/images/broken-chain.jpg" alt="Broken Chain">
  <figcaption>A system is as safe as its weakest component.</figcaption>
</figure>

In order to answer this question, I won't go deep into the details of what LXC and Docker are. The web is full of information on [namespaces](http://en.wikipedia.org/wiki/Cgroups#NAMESPACE-ISOLATION) and [cgroups](http://en.wikipedia.org/wiki/Cgroups). Rather, I'd like to show what LXC and Docker can do, what they cannot do, and what their default configuration allows them to do. My hope is to provide a quick checklist for those who want to go with LXC/Docker, but are unsure on what they need to pay attention to.

## What LXC and Docker can do

As we all know, LXC confines processes mainly thanks to two Linux kernel features: namespaces and cgroups. These provide ways to control and limit access to resource such as memory or filesystem. So, for example, you can limit the bandwidth used by processes inside a container, you can limit the priority of the CPU scheduler, and so on.

As it is well known, processes inside a LXC guest cannot:

 * directly interact with the host processes, or with other LXC containers;
 * access the root filesystem, unless configured otherwise;
 * access special devices (block devices, network interfaces, ...), unless configured otherwise;
 * mount arbitrary filesystems;
 * execute special `ioctl`s, special syscalls or special interrupts, that would affect the behavior host.

And at the same time, processes inside an LXC guest can find an environment that is perfectly suitable to run a working operating system: I can run init, I can read from `/proc`, I can access the internet.

This is most of what LXC can do, and it's also what you get by default. Docker (when used with the LXC backend) is a wrapper around LXC that provides utilities for easy deployment and management of the containers, so **everything that applies to LXC, applies to Docker too**.

If this sounds great, then beware that there are the things you should know...

## You need a security context

LXC is somewhat incomplete. What I mean is that some parts of special filesystems like procfs or sysfs are not faked. For example, as of now, I can successfully change the value of host's `/proc/sys/kernel/panic` or `/sys/class/thermal/cooling_device0/cur_state`.

The reason why LXC is "incomplete" doesn't really matter (it's actually the kernel to be incomplete, but anyhow...). What matters is that certain nasty actions can be forbade, not by LXC itself, but by an AppArmor/SELinux profile that blocks read and write access certain `/proc` and `/sys` components. The AppArmor rules were shipped in Ubuntu since 12.10 (Quantal), and have been included upstream since early 2014, together with the SELinux rules.

Therefore, **a security context like AppArmor or SELinux is required to run LXC safely**. Without it, the root user inside a guest can take control of the host.

Check that AppArmor or SELinux are running and are configured properly. If you want to go with Grsecurity, then remember to configure it manually.

## Limit resource consumption

LXC offers ways to limit resource usage, but no special restrictions are put in place by default. **You have to configure them by yourself.**

With the default configuration, I can run fork-bombs, request huge memory maps, keep all CPUs busy, doing high loads of I/O. All of this without special privileges. Remember this when running untrusted code.

<figure>
  <img src="{static}/images/memory-usage.png" alt="Uncontrolled memory consumption">
</figure>

To limit resource consumption in LXC, open the configuration file for your container and set the `lxc.cgroup.<system>` values you need.

For example, if you want to limit the container memory usage to 512 MiB, set `lxc.cgroup.memory.limit_in_bytes = 512M`. Note that the container with that option, once it exceeds the 512 MiB cap, will start using the swap without limits. If this is not what you want, then set `lxc.cgroup.memory.memsw.max_usage_in_bytes = 512M`. Note that to use both options you may need to add `cgroup_enable=memory` and `swapaccount=1` to the kernel command line.

To have an overview of all possible options, check out [Red Hat's documentation](https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux/6/html/Resource_Management_Guide/ch-Subsystems_and_Tunable_Parameters.html) or the [Kernel documentation](https://www.kernel.org/doc/Documentation/cgroups/).

With Docker, the story is similar: just use `--lxc-conf` from the command line to set LXC's options.

## Limit disk usage

Something that LXC cannot do is limiting mass storage usage. Luckily, **[LXC integrates nicely with LVM](https://www.stgraber.org/2013/12/27/lxc-1-0-container-storage/)** (and brtfs, and zfs, and overlayfs), and you can use that for easily limiting disk usage. You can, for example, create a logical volume for each of your guests, and give that volume a limited size, so that space usage inside a guest cannot grow indefinitely.

The same [holds for Docker](http://developerblog.redhat.com/2014/09/30/overview-storage-scalability-docker/).

## Pay attention at `/dev/random`

**Processes inside LXC guests**, by default, can read from `/dev/random` and **can consume the entropy of the host**. This may cause troubles if you need big amounts of randomness (to generate keys or whatever).

If this is something that you don't want, then configure LXC so that it [denies access to the character devices](https://wiki.archlinux.org/index.php/Linux_Containers#Cgroups_device_configuration) `1:8` (random) and `1:9` (urandom). Denying access to the path `/dev/random` is not enough, as `mknod` is allowed inside guests.

Note however that doing so may break many applications inside the LXC guest that need randomness. Maybe consider using a different machine for processes that require randomness for security purposes.

## Use unprivileged containers

**Containers can be [run from an unprivileged user](https://www.stgraber.org/2014/01/17/lxc-1-0-unprivileged-containers/)**. This means UID 0 of the guest can't match UID 0 of the host, and many potential security holes can't simply be exploited. Unfortunately, [Docker has not support for unprivileged containers](https://github.com/docker/docker/issues/2918) yet.

However, if Docker is not a requirement and you can do well with LXC, start experimenting with unprivileged containers and consider using them in production.

Programs like Apache will complain that it's unable to change its ulimit (because setting the ulimit is a privilege of the real root user). If you need to run programs that require special privileges, either configure them so that they do not complain, or consider using [capabilities](http://linux.die.net/man/7/capabilities) (but do not abuse them, and be cautious, or you risk introducing more problems than the ones your are trying to solve!)

## Conclusion

LXC, Docker and the entire ecosystem around them can be considered quite mature and stable. They're surely production ready, and, if the right configuration is put in place, it can be pretty difficult to cause troubles to the host.

However, whether they can be considered secure or not is up to you: **what are you using containers for? Who are you giving access to? What privileges are you giving, what actions are you restricting?**

Always remember what LXC and Docker do by default, and what they do not do, especially when you use them to run untrusted code. Those that I have listed may only be a few of the problems that LXC, Docker and friends may expose. Remember to carefully review your configuration before opening the doors to others.

## Further reading

If you liked this article, you'll find these ones interesting too:

* [Containers & Docker: how secure are they?](http://blog.docker.com/2013/08/containers-docker-how-secure-are-they/), from the Docker blog.
* Stéphane Graber's [Security features](https://www.stgraber.org/2014/01/01/lxc-1-0-security-features/) from his [LXC 1.0: Blog post series](https://www.stgraber.org/2013/12/20/lxc-1-0-blog-post-series/).
