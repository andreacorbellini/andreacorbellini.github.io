Title: Running Ubuntu Snappy inside Docker
Date: 2015-03-25 20:46
Author: andreacorbellini
Category: cloud
Tags: docker, snappy, ubuntu, ubuntu core, xkcd
Slug: running-ubuntu-snappy-inside-docker
Status: published

Many of you may have already heard of [Ubuntu Core](https://developer.ubuntu.com/en/snappy/). For those who haven't, it's a minimal Ubuntu version, running only a few essential services and ships with a new package manager (snappy) that provides *transactional* updates. Ubuntu Core provides a lightweight base operating system which is fast to deploy and easy to maintain up to date. It also uses a nice [security model](https://wiki.ubuntu.com/SecurityTeam/Specifications/SnappyConfinement).

All these characteristics make it particularly appealing for the cloud. And, in fact, people are starting considering it for building their (micro)services architectures. Some weeks ago, a user on Ask Ubuntu asked: [Can I run Snappy Ubuntu Core as a guest inside Docker?](http://askubuntu.com/questions/566736/can-i-run-snappy-ubuntu-core-as-a-guest-inside-docker/577248) The problem is that Ubuntu Core does not ship with an official Docker image that we can pull, so we are forced to set it up manually. Here's how.

## Creating the Docker image

### Step 1: get the latest Ubuntu Core

As of writing, the latest Ubuntu Core image is alpha 3 and can be downloaded with:

    :::console
    $ wget http://cdimage.ubuntu.com/ubuntu-core/releases/alpha-3/ubuntu-core-WEBDM-alpha-03_amd64-generic.img.xz

(If you browse to [cdimage.ubuntu.com](http://cdimage.ubuntu.com/ubuntu-core/releases/alpha-3/), you can also find the signed hashsums.)

The downloaded image is XZ-compressed and we need to extract it:

    :::console
    $ unxz ubuntu-core-WEBDM-alpha-03_amd64-generic.img.xz

### Step 2: connect the image using qemu-nbd

The file we have just downloaded and extracted is a filesystem dump. The previous version of the image (Alpha 2) was a QCOW2 image (the format used by QEMU). In order to access its contents, we have a few options. Here I'll show one that works with both filesystem dumps and QCOW2 images. The trick consists in using `qemu-nbd` (a tool from the [qemu-utils](https://apps.ubuntu.com/cat/applications/qemu-utils/) package):

    :::console
    # qemu-nbd -rc /dev/nbd0 ubuntu-core-WEBDM-alpha-03_amd64-generic.img

This command will create a virtual device named `/dev/nbd0`, with virtual partitions named `/dev/nbd0p1`, `/dev/nbd0p2`, ... Use `fdisk -l /dev/nbd0` to get an idea of what partitions are inside the QCOW2 image.

### Step 3: mount the filesystem

The partition we are interested in is `/dev/nbd0p3`, so we need to mount it:

    :::console
    # mkdir nbd0p3
    # mount -r /dev/nbd0p3 nbd0p3

### Step 4: create a base Docker image

As suggested on the [Docker documentation](https://docs.docker.com/articles/baseimages/), creating a base Docker image from a directory is pretty straightforward:

    :::console
    # tar -C nbd0p3 -c . | docker import - ubuntu-core alpha-3

Our newly created image will now appear when running `docker images`:

    :::console
    # docker images
    REPOSITORY          TAG                 IMAGE ID            CREATED             VIRTUAL SIZE
    ubuntu-core         alpha-3             f6df3c0e2d74        5 seconds ago       543.5 MB

Let's verify if we did a good job:

    :::console
    # docker run ubuntu-core:alpha-3 snappy
    Usage:snappy [-h] [-v]
                 {info,versions,search,update-versions,update,rollback,install,uninstall,tags,config,build,booted,chroot,framework,fake-version,nap}
                 ...

Yes! We have successfully added Ubuntu Core to the available Docker images and we have run our first snappy container!

## Installing and running software

Without wasting too many words, here's how to install and run the `xkcd-webserver` snappy package inside docker:

    :::console
    # docker run -p 8000:80 ubuntu-core:alpha-3 /bin/sh -c 'snappy install xkcd-webserver && cd /apps/xkcd-webserver/0.3.1 && ./bin/xkcd-webserver'
    WARN: AppArmor not available when processing AppArmor hook
    Failed to get D-Bus connection: Operation not permitted
    Failed to get D-Bus connection: Operation not permitted

    ** (process:13): WARNING **: user.vala:637: Can not connect to logind
    xkcd-webserver     21 kB     [======================================]    OK
    WARNING: failed to connect to dbus: org.freedesktop.DBus.Error.FileNotFound: Failed to connect to socket /var/run/dbus/system_bus_socket: No such file or directory
    Part            Tag   Installed  Available  Fingerprint     Active
    xkcd-webserver  edge  0.3.1      -          3a9152b8bff494  *

Now, if you visit http://localhost:8000/ you should see a random XKCD comic.

If you have payed attention, you may have noticed a few warnings about AppArmor, DBus and logind. The reason why you are seeing these warnings is pretty simple: we did not start neither AppArmor nor DBus nor logind. Now, generally speaking, we could run init inside Docker and fix these and other warnings. However that's not what Docker is meant for. So if you want to run AppArmor or similar stuff *from inside* Docker or LXC, then probably you should consider virtualization.

## Dockerfile

Once you have created the base Docker image, you can start creating some `Dockerfile`s, if you need to. Here's an example:

    :::dockerfile
    FROM ubuntu-core:alpha-3
    RUN snappy install xkcd-webserver
    EXPOSE 8000:80
    CMD cd /apps/xkcd-webserver/0.3.1 && ./bin/xkcd-webserver

This `Dockerfile` does the same job as the previous command: it installs and runs `xkcd-webserver` on port 8000. In order to use it, first build it:

    :::console
    # docker build -t xkcd-webserver .

Check that it has been correctly installed:

    :::console
    # docker images
    REPOSITORY          TAG                 IMAGE ID            CREATED             VIRTUAL SIZE
    xkcd-webserver      latest              260e0116e9e3        3 minutes ago       543.5 MB
    ubuntu-core         alpha-3             f6df3c0e2d74        About an hour ago   543.5 MB

Then run it:

    :::console
    # docker run xkcd-webserver

Again, you should see a random XKCD comic on [http://localhost:8000/](http://localhost:8000/).

## Conclusion

That's all folks! I hope you enjoyed this tiny guide, and if you need help, please ask a question on Ask Ubuntu with the [ubuntu-core tag](http://askubuntu.com/questions/tagged/ubuntu-core), which I'm subscribed to.
