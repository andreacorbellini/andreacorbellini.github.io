Title: How to use the same DNS for all connections in Ubuntu (and other network privacy tricks)
Date: 2020-04-28 06:30
Author: andreacorbellini
Category: ubuntu
Tags: ubuntu, systemd, resolved, network-manager, dns, mac-address, privacy
Slug: ubuntu-global-dns
Status: published

# Problem

Currently Ubuntu does not offer an easy way to set up a "global" DNS for all network connections: whenever you connect to a new WiFi network, if you don't want to use the DNS server provided by the WiFi, you are forced to go to the network settings and manually set your preferred DNS server.

With this brief guide I want to show how you can setup a global DNS to be used for _all_ the WiFi and network connections, both old and new ones. I will also show you how to use DNSSEC, DNS-over-TLS and randomized MAC addresses for all connections.

This guide is written for Ubuntu 20.04, but in general it will work on every distribution using systemd-resolved and NetworkManager.

# Step 1: setup the Global DNS in resolved

In Ubuntu (as well as many other distributions), DNS is managed by systemd-resolved. Its configuration is in `/etc/systemd/resolved.conf`. Open that file and add a `DNS=` line inside the `[Resolve]` section listing your preferred DNS servers. For example, if you want to use [`1.1.1.1`](https://1.1.1.1/), your `resolved.conf` should look like this:

    [Resolve]
    DNS=1.1.1.1 1.0.0.1 2606:4700:4700::1111 2606:4700:4700::1001
    #FallbackDNS=
    #Domains=
    #LLMNR=no
    #MulticastDNS=no
    #Cache=yes
    #DNSStubListener=yes
    #ReadEtcHosts=yes

Once you are done with the changes, reload systemd-resolved:

    sudo systemctl restart systemd-resolved.service

You can check your changes with `resolvectl status`: you should see your DNS servers on top of the output, under the _Global_ section:

    $ resolvectl status
    Global
           LLMNR setting: no
    MulticastDNS setting: no
      DNSOverTLS setting: opportunistic
          DNSSEC setting: allow-downgrade
        DNSSEC supported: no
      Current DNS Server: 1.1.1.1
             DNS Servers: 1.1.1.1
                          1.0.0.1
                          2606:4700:4700::1111
                          2606:4700:4700::1001
    ...

This however won't be enough to use that DNS! In fact, the _Global_ DNS of systemd-resolved is just a default option that is used whenever no DNS servers are configured for an interface. When you connect to a WiFi network, NetworkManager will ask the access point for a list of DNS servers and will communicate that list to systemd-resolved, effectively overriding the settings that we just edited. If you scroll down the output of `resolvectl status`, you will see the DNS servers added by NetworkManager. We have to tell NetworkManager to stop doing that.

# Step 2: Disable DNS processing in NetworkManager

In order for systemd-resolved to consider our global DNS, we need to tell NetworkManager not to provide any DNS information for new connections. Doing that is easy: just create a new file `/etc/NetworkManager/conf.d/dns.conf` (or any name you like) with this content:

    [main]
    # do not use the dhcp-provided dns servers, but rather use the global
    # ones specified in /etc/systemd/resolved.conf
    dns=none
    systemd-resolved=false

To apply the settings either run restart your computer or run:

    sudo systemctl reload NetworkManager.service

Now, when you connect to a new network connection, NetworkManager won't push the list of DNS servers to systemd-resolved and only the global ones will be used. If you check `resolvectl status`, you should see that, for every interface, there is _no_ DNS server specified. If you specified `1.1.1.1` as your DNS servers, then you can also head over to [https://1.1.1.1/help](https://1.1.1.1/help) to verify that they've been correctly set up.

# DNSSEC and DNS-over-TLS

If you would like to enable DNSSEC and/or DNS-over-TLS, the file to edit is `/etc/systemd/resolved.conf`. You can add the following options:

* `DNSSEC=true` if you want all queries to be DNSSEC-validated. The default is `DNSSEC=allow-downgrade`, which attempts to use DNSSEC if it works properly, and falls back to disabling validation otherwise.
* `DNSOverTLS=true` if you want all queries to go through TLS. You can also specify `DNSOverTLS=opportunistic` to attempt to use TLS if it supported, and fall back to the plaintext DNS protocol if it's not.

With those options, my `/etc/systemd/resolved.conf` looks like this:

    [Resolve]
    DNS=1.1.1.1 1.0.0.1 2606:4700:4700::1111 2606:4700:4700::1001
    #FallbackDNS=
    #Domains=
    #LLMNR=no
    #MulticastDNS=no
    DNSSEC=true
    DNSOverTLS=opportunistic
    #Cache=yes
    #DNSStubListener=yes
    #ReadEtcHosts=yes

Note that I'm using `DNSOverTLS=opportunistic` because I found that some access points with captive portals don't work properly when using `DNSOverTLS=true`. Also note that `DNSSEC=true` may cause some pain because there are still many misconfigured domain records out there that will make make DNSSEC validation fail.

Like before, to apply the changes, run:

    sudo systemctl restart systemd-resolved.service

And to verify the changes:

    resolvectl status

If you're using `1.1.1.1`, you can also go to [https://1.1.1.1/help](https://1.1.1.1/help) to verify DNS-over-TLS.

# Random MAC address

NetworkManager supports 3 options to have a random MAC address (also known as "cloned" or "spoofed" MAC address):

1. `wifi.scan-rand-mac-address` controls the MAC address used when scanning for WiFi devices. This goes into the `[device]` section
1. `wifi.cloned-mac-address` controls the MAC address for WiFi connections. This goes into the `[connection]` section
1. `ethernet.cloned-mac-address` controls the MAC address for Ethernet connections. This goes into the `[connection]` section

The first option can take either `yes` or `no`. The last two can take various values, but if you want a randomized MAC address you are interested in these two:

* `random`: generate a new random MAC address each time you establish a connection
* `stable`: this generates a MAC address that is kinda random (it's a hash), but will be reused when you connect to the same network again.

`random` is better if you don't want to be tracked, but it has the disadvantage that captive portals won't remember you. Instead `stable` allows captive portals to remember you and therefore won't show up whenever you reconnect.

Whatever options you want to go with, put them into a file `/etc/NetworkManager/conf.d/mac.conf` (or any other name you like). Mine looks like this:

    [device]
    # use a random mac address when scanning for wifi networks
    wifi.scan-rand-mac-address=yes

    [connection]
    # use a random mac address when connecting to a network
    ethernet.cloned-mac-address=random
    wifi.cloned-mac-address=random

To apply the settings either run restart your computer or run:

    sudo systemctl reload NetworkManager.service

You can test your changes with:

    ip link
