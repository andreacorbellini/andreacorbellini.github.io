Title: Running the operating system that you're currently using in a virtual machine (with Secure Boot and TPM emulation)
Date: 2023-11-19 16:33
Author: andreacorbellini
Category: information-technology
Slug: running-current-os-inside-vm
Status: published

In this article I will show you how to start your current operating system
inside a virtual machine. That is: launching the operating system (with all
your settings, files, and everything), inside a virtual machine, while you're
using it.

This article was written for Ubuntu, but it can be easily adapted to other
distributions, and with appropriate care it can be adapted to non-Linux kernels
and operating systems as well.

# Motivation

Before we start, why would a sane person want to do this in the first place?
Well, here's why I did it:

*   **To test changes that affect Secure Boot without a reboot.**

    Recently I was doing some experiments with Secure Boot and the Trusted
    Platform Module (TPM) on a new laptop, and I got frustrated by how time
    consuming it was to test changes to the boot chain. Every time I modified a
    file involved during boot, I would need to reboot, then log in, then
    re-open my terminal windows and files to make more modifications... Plus,
    whenever I screwed up, I would need to manually recover my system, which
    would be even more time consuming.

    I thought that I could speed up my experiments by using a virtual machine
    instead.

*   **To predict the future TPM state (in particular, the values of PCRs 4, 5,
    8, and 9) after a change, without a reboot.**

    I wanted to predict the values of my TPM PCR banks after making changes to
    the bootloader, kernel, and initrd. Writing a script to calculate the PCR
    values automatically is in principle not that hard (and I actually did it
    before, in a different context), but I wanted a robust, generic solution
    that would work on most systems and in most situations, and emulation was
    the natural choice.

*   And, of course, **just for the fun of it!**

To be honest, I'm not a big fan of Secure Boot. The reason why I've been
working on it is simply that it's the standard nowadays and so I have to stick
with it. Also, there are no real alternatives out there to achieve the same
goals. I'll write an article about Secure Boot in the future to explain the
reasons why I don't like it, and how to make it work better, but that's another
story...

# Procedure

The procedure that I'm going to describe has 3 main steps:

1. create a copy of your drive
1. emulate a TPM device using swtpm
1. emulate the system with QEMU

I've tested this procedure on Ubuntu 23.04 (Lunar) and 23.10 (Mantic), but it
should work on any Linux distribution with minimal adjustments. The general
approach can be used for any operating system, as long as appropriate
replacements for QEMU and swtpm exist.

## Prerequisites

Before we can start, we need to install:

- [QEMU](https://www.qemu.org/): a virtual machine emulator
- [swtpm](https://github.com/stefanberger/swtpm/wiki): a TPM emulator
- [OVMF](https://wiki.ubuntu.com/UEFI/OVMF): a UEFI firmware implementation

On a recent version of Ubuntu, these can be installed with:

```
sudo apt install qemu-system-x86 ovmf swtpm
```

Note that OVMF only supports the x86\_64 architecture, so we can only emulate
that. If you run a different architecture, you'll need to find another UEFI
implementation that is not OVMF (but I'm not aware of any freely available
ones).

## Create a copy of your drive

We can decide to either:

* **Choice #1: [run only the components involved early at
  boot](#early-boot-components-only) (shim, bootloader, kernel, initrd).** This
  is useful if you, like me, only need to test those components and how they
  affect Secure Boot and the TPM, and don't really care about the rest (the
  init process, login manager, ...).

* **Choice #2: [run the entire operating system](#entire-system).** This can
  give you a fully usable operating system running inside the virtual machine,
  but may also result in some instability inside the guest (because we're
  giving it a filesystem that is in use), and may also lead to some data loss
  if we're not careful and make typos. Use with care!

### Choice #1: Early boot components only {#early-boot-components-only}

If we're interested in the early boot components only, then we need to make a
copy the following from our drive: the GPT partition table, the EFI partition,
and the `/boot` partition (if we have one). Usually all these 3 pieces are at
the "start" of the drive, but this is not always the case.

To figure out where the partitions are located, run:

```
sudo parted -l
```

On my system, this is the output:

```
Model: WD_BLACK SN750 2TB (nvme)
Disk /dev/nvme0n1: 2000GB
Sector size (logical/physical): 512B/512B
Partition Table: gpt
Disk Flags:

Number  Start   End     Size    File system  Name  Flags
 1      1049kB  525MB   524MB   fat32              boot, esp
 2      525MB   1599MB  1074MB  ext4
 3      1599MB  2000GB  1999GB                     lvm
```

In my case, the partition number 1 is the EFI partition, and the partition
number 2 is the `/boot` partition. If you're not sure what partitions to look
for, run `mount | grep -e /boot -e /efi`. Note that, on some distributions
(most notably the ones that use `systemd-boot`), a `/boot` partition may not
exist, so you can leave that out in that case.

Anyway, in my case, I need to copy the first 1599 MB of my drive, because
that's where the data I'm interested in ends: those first 1599 MB contain the
GPT partition table (which is always at the start of the drive), the EFI
partition, and the `/boot` partition.

Now that we have identified how many bytes to copy, we can copy them to a file
named `drive.img` with `dd` (maybe after running `sync` to make sure that all
changes have been committed):

```
# replace '/dev/nvme0n1' with your main drive (which may be '/dev/sda' instead),
# and 'count' with the number of MBs to copy
sync && sudo -g disk dd if=/dev/nvme0n1 of=drive.img bs=1M count=1599 conv=sparse
```

### Choice #2: Entire system {#entire-system}

If we want to run our entire system in a virtual machine, then I would
recommend creating a QEMU copy-on-write (COW) file:

```
# replace '/dev/nvme0n1' with your main drive (which may be '/dev/sda' instead)
sudo -g disk qemu-img create -f qcow2 -b /dev/nvme0n1 -F raw drive.qcow2
```

This will create a new copy-on-write image using `/dev/nvme0n1` as its "backing
storage". Be very careful when running this command: you don't want to mess up
the order of the arguments, or you might end up writing to your storage device
(leading to data loss)!

The advantage of using a copy-on-write file, as opposed to copying the whole
drive, is that this is much faster. Also, if we had to copy the entire drive,
we might not even have enough space for it (even when using sparse files).

The big drawback of using a copy-on-write file is that, because our main drive
likely contains filesystems that are mounted read-write, any modification to
the filesystems on the host may be perceived as data corruption on the guest,
and that in turn may cause all sort of bad consequences inside the guest,
including kernel panics.

Another drawback is that, with this solution, later we will need to give QEMU
permission to *read* our drive, and if we're not careful enough with the
commands we type (e.g. we swap the order of some arguments, or make some
typos), we may potentially end up *writing* to the drive instead.

## Emulate a TPM device using swtpm

There are various ways to run the swtpm emulator. Here I will use the "vTPM
proxy" way, which is not the easiest, but has the advantage that the emulated
device will look like a real TPM device not only to the guest, but also to the
host, so that we can inspect its PCR banks (among other things) from the host
using familiar tools like `tpm2_pcrread`.

First, enable the `tpm_vtpm_proxy` module (which is not enabled by default on
Ubuntu):

```
sudo modprobe tpm_vtpm_proxy
```

If that worked, we should have a `/dev/vtpmx` device. We can verify its
presence with:

```
ls /dev/vtpmx
```

swtpm in "vTPM proxy" mode will interact with `/dev/vtpmx`, but in order to do
so it needs the `sys_admin` capability. On Ubuntu, swtpm ships with this
capability explicitly disabled by AppArmor, but we can enable it with:

```
sudo sh -c "echo '  capability sys_admin,' > /etc/apparmor.d/local/usr.bin.swtpm"
systemctl reload apparmor
```

Now that `/dev/vtpmx` is present, and swtpm can talk to it, we can run swtpm
in "vTPM proxy" mode:

```
sudo mkdir /tpm/swtpm-state
sudo swtpm chardev --tpmstate dir=/tmp/swtpm-state --vtpm-proxy --tpm2
```

Upon start, swtpm should create a new `/dev/tpmN` device and print its name on
the terminal. On my system, I already have a real TPM on `/dev/tpm0`, and
therefore swtpm allocates `/dev/tpm1`.

The emulated TPM device will need to be readable and writeable by QEMU, but the
emulated TPM device is by default accessible only by root, so either we run
QEMU as root (not recommended), or we relax the permissions on the device:

```
# replace '/dev/tpm1' with the device created by swtpm
sudo chmod a+rw /dev/tpm1
```

Make sure not to accidentally change the permissions of your real TPM device!

## Emulate the system with QEMU

Inside the QEMU emulator, we will run the OVMF UEFI firmware. On Ubuntu, the
firmware comes in 2 flavors:

* with Secure Boot enabled (`/usr/share/OVMF/OVMF_CODE_4M.ms.fd`), and
* with Secure Boot disabled (in `/usr/share/OVMF/OVMF_CODE_4M.fd`)

(There are actually even more flavors, see [this AskUbuntu
question](https://askubuntu.com/q/1409590) for the details.)

In the commands that follow I'm going to use the Secure Boot flavor, but if you
need to disable Secure Boot in your guest, just replace `.ms.fd` with `.fd` in
all the commands below.

To use OVMF, first we need to copy the EFI variables to a file that can be read
& written by QEMU:

```
cp /usr/share/OVMF/OVMF_VARS_4M.ms.fd /tmp/
```

This file (`/tmp/OVMF_VARS_4M.ms.fd`) will be the equivalent of the EFI flash
storage, and it's where OVMF will read and store its configuration, which is
why we need to make a copy of it (to avoid modifications to the original file).

Now we're ready to run QEMU:

*   If you [copied only the early boot files (choice
    #1)](#early-boot-components-only):

        # replace '/dev/tpm1' with the device created by swtpm
        qemu-system-x86_64 \
          -accel kvm \
          -machine q35,smm=on \
          -cpu host \
          -smp cores=4,threads=1 \
          -m 4096 \
          -vga virtio \
          -bios /usr/share/ovmf/OVMF.fd \
          -drive if=pflash,unit=0,format=raw,file=/usr/share/OVMF/OVMF_CODE_4M.ms.fd,readonly=on \
          -drive if=pflash,unit=1,format=raw,file=/tmp/OVMF_VARS_4M.ms.fd \
          -drive if=virtio,format=raw,file=drive.img \
          -tpmdev passthrough,id=tpm0,path=/dev/tpm1,cancel-path=/dev/null \
          -device tpm-tis,tpmdev=tpm0

*   If you have [a copy-on-write file for the entire system (choice
    #2)](#entire-system):

        # replace '/dev/tpm1' with the device created by swtpm
        sudo -g disk qemu-system-x86_64 \
          -accel kvm \
          -machine q35,smm=on \
          -cpu host \
          -smp cores=4,threads=1 \
          -m 4096 \
          -vga virtio \
          -bios /usr/share/ovmf/OVMF.fd \
          -drive if=pflash,unit=0,format=raw,file=/usr/share/OVMF/OVMF_CODE_4M.ms.fd,readonly=on \
          -drive if=pflash,unit=1,format=raw,file=/tmp/OVMF_VARS_4M.ms.fd \
          -drive if=virtio,format=qcow2,file=drive.qcow2 \
          -tpmdev passthrough,id=tpm0,path=/dev/tpm1,cancel-path=/dev/null \
          -device tpm-tis,tpmdev=tpm0

    Note that this last command makes QEMU run as the `disk` group: on Ubuntu,
    this group has the permission to read *and write* all storage devices, so
    be careful when running this command, or you risk losing your files
    forever! If you want to add more safety, you may consider using an
    [ACL](https://manpages.ubuntu.com/manpages/mantic/en/man5/acl.5.html) to
    give the user running QEMU read-only permission to your backing storage.

In either case, after launching QEMU, our operating system should boot...
while running inside itself!

In some circumstances though it may happen that the wrong operating system is
booted, or that you end up at the EFI setup screen. This can happen if your
system is not configured to boot from the "first" EFI entry listed in the EFI
partition. Because the boot order is not recorded anywhere on the storage
device (it's recorded in the EFI flash memory), of course OVMF won't know which
operating system you intended to boot, and will just attempt to launch the
first one it finds. You can use the EFI setup screen provided by OVMF to change
the boot order in the way you like. After that, changes will be saved into the
`/tmp/OVMF_VARS_4M.ms.fd` file on the host: you should keep a copy of that file
so that, next time you launch QEMU, you'll boot directly into your operating
system.

## Reading PCR banks after boot

Once our operating system has launched inside QEMU, and after the boot process
is complete, the PCR banks will be filled and recorded by swtpm.

If we choose to [copy only the early boot files (choice
\#1)](#early-boot-components-only), then of course our operating system won't be
*fully* booted: it'll likely hang waiting for the root filesystem to appear,
and may eventually drop to the initrd shell. None of that really matters if all
we want is to see the PCR values stored by the bootloader.

Before we can extract those PCR values, we first need to stop QEMU (Ctrl-C is
fine), and then we can read it with `tpm2_pcrread`:

```
# replace '/dev/tpm1' with the device created by swtpm
tpm2_pcrread -T device:/dev/tpm1
```

Using the method described here in this article, PCRs 4, 5, 8, and 9 inside the
emulated TPM *should* match the PCRs in our real TPM. And here comes an
interesting application of this method: if we upgrade our bootloader or kernel,
and we want to know the *future* PCR values that our system will have after
reboot, we can simply follow this procedure and obtain those PCR values without
shutting down our system! This can be especially useful if we use TPM sealing:
we can reseal our secrets and make them unsealable at the next reboot without
trouble.

## Restarting the virtual machine

If we want to restart the guest inside the virtual machine, and obtain a
consistent TPM state every time, we should start from a "clean" state every
time, which means:

1. restart swtpm
1. recreate the `drive.img` or `drive.qcow2` file
1. launch QEMU again

If we don't restart swtpm, the virtual TPM state (and in particular the PCR
banks) won't be cleared, and new PCR measurements will simply be added on top
of the existing state. If we don't recreate the drive file, it's possible that
some modifications to the filesystems will have an impact on the future PCR
measurements.

We don't necessarily need to recreate the `/tmp/OVMF_VARS_4M.ms.fd` file every
time. In fact, if you need to modify any EFI setting to make your system
bootable, you might want to preserve it so that you don't need to change EFI
settings at every boot.

# Automating the entire process

I'm (very slowly) working on turning this entire procedure into a script, so
that everything can be automated. Once I find some time I'll finish the script
and publish it, so if you liked this article, stay tuned, and let me know if
you have any comment/suggestion/improvement/critique!
