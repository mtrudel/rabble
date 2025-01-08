# Rabble

Rabble is our home server / gaming PC. My goal was to have a machine that could
take over the burden of running the [various
things](https://github.com/mtrudel/pibox) we run around the house, and also to
act as a couch gaming PC with enough oomph to play demanding games (MSFS 2024,
mostly). Some stuff about it:

* It runs multiple VMs on a [Proxmox](https://www.proxmox.com/) host
* There's a Windows VM ('broffina') for gaming, which accesses the GPU via PCI
  passthrough ('VFIO'). [Benchmarks](https://browser.geekbench.com/user/522804)
  place it around 95-98% of bare metal performance
* The primary Linux VM ('blathers') is a work in progress, and will be bringing
  over almost all of the work in my [pibox](https://github.com/mtrudel/pibox)
  project
* We have it set up for couch gaming, with some extra provision for
  auto-switching the TV and optimized power consumption when the Windows VM is
  off (which is most of the time)
* It's Animal Crossing themed! When we were putting together the [part
  list](https://ca.pcpartpicker.com/b/nVJfrH), we
  noticed that the palette looked a lot like the colours in ACNH, so we doubled down
  with some fun decorating (more below), and used the names of our
  family island ('rabble') as the host OS hostname, and our favorite villagers
  as guest hostnames

This repo is a collection of notes around the planning, building, configuration
and maintenance of the machine, mostly for my own records but also as a source
if others want to build a similar setup.

# Hardware

I spent a little less than a month putting together the [part
list](https://ca.pcpartpicker.com/b/nVJfrH), focusing on
a high-end-but-still-cost-conscious approach that I later found out mapped
almost perfectly onto the [Logical Increments 'outstanding'
tier](https://www.logicalincrements.com).

Not much to say about this; it's a pretty standard PC (despite the absurd case)
and goes together without any real fuss. All of the parts other than the CPU
cooler would port over to any standard SFF case if you're looking for something
more conventional.

### Decorating

We designed the Nook print vinyl sticker & had it printed at StickerYou. The Tom
Nook figurine is an Amiibo. We also bought a [couple of light
bars](https://www.aliexpress.com/item/1005005989319012.html) from AliExpress, and
after some failed experiments trying to control them in software, I picked up a
[standalone RGB controller](https://www.aliexpress.com/item/1005007513322954.html)
that is powered directly off the PSU and is stuck on the bottom of the case for
the rare time that we actually want to have the RGB lighting on.

### BIOS

As this build is vulnerable to Intel's recent [CPU self-destruct
bug](https://www.pcmag.com/explainers/intels-raptor-lake-desktop-cpu-bug-what-to-know-what-to-do-now),
the first thing we did at first boot was to update the BIOS to the latest
version which is supposedly safe.

It's currently running the following BIOS settings (notes are somewhat terse but
you can figure it out):

* Reset factory defaults
* Ai Tweaker
  * 'Ai Overclock Tuner' to XMP 1
    * Ensure memory is 6000 CL30
  * Intel Adaptive Boost Technology to Enabled
* Advanced / Platform Misc Configuration
  * Native ASPN to Enabled
  * DMI Link ASPM Control to L1
  * ASPM to L1
  * L1 Substates to L1.1 & L1.2
  * DMI ASPM to ASPM L1
  * DMI Gen3 ASPM to ASPM L1
  * PEG - ASPM to L0sL1
* Advanced / Platform Misc Configuration / CPU - Power Maangement Control
  * CPU C-states to Enabled
  * Package C State Limit to C10
* Advanced / PCH Storage Configuration
  * Aggressive LPM Support to Enabled
* Advanced / APM Configuration
  * Restore AC Power Loss to Last State
* Advanced / Thermal Configuration
  * Intel Dynamic Tuning Technology to Enabled
* Advanced / Onbaord Devices Configuration
  * HD Audio to Disabled
  * When system is in working State to Stealth Mode
* Monitor
  * CPU Temperature LED Switch to Disabled
  * CPU fan:
    * Step up/down to Level 1
  * Chassis fan (top fan):
    * Mode to Manual
    * Step up.down to Level 2
    * Values to 70 100 60 60 50 40 40 20
  * AIO fan (bottom & back fan):
    * Mode to Manual
    * Step up/down to Level 3
    * Pump Speed Lower Limit to 200 RPM
    * Values to 70 60 60 40 50 20 40 0 (may not go to 0)
* Boot / Boot Configuration
  * Wait for F1 If Error to Disable
  * Setup Mode to Advanced Mode

### Burn In / Benchmarking

* I ran four cycles of memtest86 (the version on Ubuntu's install image) which all passed 100%
* Installed a temporary Ubuntu install that I didn't feel bad about trashing during benchmarking
* Ran a handful of runs of Geekbench on the Linux host to establish baseline Linux
  benchmarks
* Installed a scratch bare-metal Windows 11 install to establish baseline Windows benchmarks
  (Geekbench is notorious for returning different numbers in Windows and Linux
  on identical hardware; see [my
  results](https://browser.geekbench.com/user/522804) as an example)
* Ran a few hours of s-tui while ensuring temperatures stayed below 85C or so
* I used [s-tui](https://github.com/amanusk/s-tui) to fully load all cores.
  The goal is for package temps to stay below ~85C under a steady state full
  load, while still having all cores running at or near their max of 5.1GHz / 3.8GHz. If
  temperatures exceed those limits, you either need a bigger cooler or to lower
  the CPU power limit in the BIOS. In this case, because our cooler has a [ton
  of headroom](https://ncc.noctua.at/cpus/model/INTEL-Core-i5-13600K-1638) we're
  fine here. In actuality we end up with a few p-cores running at 4.9GHz in
  s-tui, but this is a pretty synthetic situation and not really worth my time
  to explore further
* Under full load, I tinkered with the fan curves in the BIOS to allow the fans
  to run as slowly as possible while still doing their job. The values in the
  BIOS section above reflect this effort

# Host OS

Installing Proxmox is pretty straightforward. Again, terse notes-to-self are
below, but you can figure it out.

### Basic install

* Run installer, select default options. Pick an IP of x.y.z.4.
* Install https://github.com/Yrlish/pve-nag-buster per instructions
* `apt update`
* `apt upgrade`
* `apt install avahi-daemon linux-cpupower lm-sensors powertop prometheus-node-exporter s-tui stress sudo zsh`
* `useradd -m -s /usr/bin/zsh mat`
* `usermod -aG sudo mat`
* `passwd mat`
* Manually copy ssh key to `~mat/.ssh`
* Disable password login in `/etc/ssh/sshd_config`
* Add the following to `/etc/sudoers.d/mat-nopasswd`
    ```
    mat ALL=(ALL) NOPASSWD: ALL
    ```
* `sensors-detect` (select defaults, add lines to modprobe)
* `systemctl enable powertop.service`
* `systemctl disable openipmi`
* Reboot

### Set up my dotfiles

* `apt install git`
* `git clone git@github.com:mtrudel/dotfiles.git`
* `cd dotfiles && ./install.zsh zsh ssh snap nvim git`

### Install Nvidia drivers

These are required to set the GPU to persistent mode when it is not passed
through to a guest. This makes a significant difference in power consumption,
bringing the machine from a ~45W idle to a ~25W idle.

This currently installs the proprietary driver, which currently (as of
565.57.01) uses about 6W less at idle than the open drivers do (this is noted in
Nvidia's release notes). If you want to install the open drivers, it suffices to
add `nvidia-kernel-open-dkms` to the `apt install nvidia-drivers-cuda
libnvidia-ml1` command below; the package dependencies are smart enough to
notice that you're bringing in the open driver source. You can also use this to
switch between the open and proprietary drivers; it doesn't even require a reboot.

* `curl -O https://developer.download.nvidia.com/compute/cuda/repos/debian12/x86_64/cuda-keyring_1.1-1_all.deb`
* `dpkg -i cuda-keyring_1.1-1_all.deb`
* `apt install proxmox-headers-6.11.0-1-pve` (as depends on your kernel version)
* `apt install nvidia-driver-cuda libnvidia-ml1`
* Make `/etc/modprobe.d/nvidia.conf` look like the following:
    ```
    blacklist nouveau
    blacklist nvidia-drm
    blacklist nvidia-modeset
    blacklist nvidiafb
    blacklist snd_hda_intel

    #options nvidia NVreg_RmMsg=":"
    options nvidia NVreg_DynamicPowerManagement=0x02
    options nvidia NVreg_EnableGpuFirmware=0
    #options nvidia-drm modeset=0
    ```
* Add the following to `/usr/local/bin/passthrough` and set 755 (we'll use
  this in our VM hook scripts later)
    ```
    #!/bin/bash

    cpupower frequency-set --governor performance > /dev/null
    cpupower set -b 0

    service nvidia-persistenced stop
    echo 0000:01:00.0 > /sys/bus/pci/devices/0000:01:00.0/driver/unbind
    echo 0000:01:00.1 > /sys/bus/pci/devices/0000:01:00.1/driver/unbind
    echo vfio-pci > /sys/bus/pci/devices/0000:01:00.0/driver_override
    echo vfio-pci > /sys/bus/pci/devices/0000:01:00.1/driver_override
    echo 0000:01:00.0 > /sys/bus/pci/drivers_probe
    echo 0000:01:00.1 > /sys/bus/pci/drivers_probe
    ```
* Add the following to `/usr/local/bin/powersave` and set 755 (we'll use
  this in our VM hook scripts later)
    ```
    #!/bin/bash

    cpupower frequency-set --governor powersave > /dev/null
    cpupower set -b 15

    if [[ ! "$(readlink /sys/bus/pci/devices/0000:01:00.0/driver)" =~ "nvidia" ]]
    then
        echo 0000:01:00.0 > /sys/bus/pci/devices/0000:01:00.0/driver/unbind
        echo 0000:01:00.1 > /sys/bus/pci/devices/0000:01:00.1/driver/unbind
        echo nvidia > /sys/bus/pci/devices/0000:01:00.0/driver_override
        echo 0000:01:00.0 > /sys/bus/pci/drivers_probe
        echo 0000:01:00.1 > /sys/bus/pci/drivers_probe
        /usr/sbin/service nvidia-persistenced start
    fi
    ```
* Run `crontab -e` as root and add `*/2 * * * * /usr/local/bin/powersave`

This sets up a cron job that runs every two minutes to make sure that the
machine is in powersave mode whenever the Windows VM isn't running. This
*should* be handled by the hook script above, but it
[seems](https://forum.proxmox.com/threads/hookscript-with-post-stop-when-the-vm-was-shutdown-from-the-vm-itself.72802/)
as if hook scripts aren't reliable if there are USB devices being passed through
(as is the case with broffina). I could also get fancy with systemd or udev
scripts here, but honestly I can't be bothered.

### TV Tweaks

This enables console autologin and embiggens the console font for better use on
a TV, and also installs CEC tools to help with turning the TV on and off. The guest OS
installs make use of this in their start/stop hook scripts.

* Run `sudo systemctl edit getty@.service` and make the file contents be:
    ```
    [Service]
    ExecStart=
    ExecStart=-/sbin/agetty --noclear --autologin mat %I $TERM
    ```
* Set `FONTFACE="Termius"` and `FONTSIZE="16x32"` in `/etc/default/console-setup`
* Add `consoleblank=30` to the `GRUB_CMDLINE_LINUX` argument in `/etc/default/grub`
* `update-grub`
* `apt install cec-utils`

# Guest OS

### Windows Guest Install

* Follow pre-setup guide at https://pve.proxmox.com/wiki/Windows_10_guest_best_practices
* Use `host` CPU type, 20 cores
* Use 48GB of RAM
* Pass through 0000:01:00.0 PCI device (PCI Express needs to be selected, as
  well as 'Use all functions')
* Enable `hugepage`, `hv*`, `aes` flags in CPU section of VM configuration
* Ensure driver CD is mounted during install
* Install vioscsi, vioserial, netKVM, balloon drivers from the driver CD
* Pick privacy options during install
* Log into to MS account
* Activate and then pick 'My hardware recently changed' option
* Install any missing drivers from base installer on driver CD
* Download and install Nvidia drivers
* Install tinyVNC as system service
* Tweak install as desired
* Add the following to `/var/lib/vz/snippets/broffina.sh` and set 755
    ```
    #!/usr/bin/env bash

    if [ "$2" == "pre-start" ]
    then
      echo "as" | /usr/bin/cec-client -o Rabble -r -s -d 1
      /usr/local/bin/passthrough
    elif [ "$2" == "post-stop" ]
    then
      echo "tx 1f:36" | /usr/bin/cec-client -o Rabble -r -s -d 1
      /usr/local/bin/powersave
    fi

    exit 0
    ```
* Edit the `/etc/pve/qemu-server/1??.conf` for the above VM and add a line like `hookscript: local:snippets/broffina.sh`
* Add the following to `/usr/local/bin/run` and set 755
    ```
    sudo /usr/sbin/qm start 1??
    ```
* Add the following to `/usr/local/bin/stop` and set 755
    ```
    sudo /usr/sbin/qm stop 1??
    ```
* Add a line like the following to the start of `/usr/local/bin/powersave`:
    ```
    # Exit if we're running a VM that uses passthrough
    /usr/sbin/qm status 1?? | grep -q running && exit 0
    ```

### Linux Guest Install

* Use `host` CPU type, 4 cores
* Use 8GB of RAM
* Use Ubuntu server install CD
* Add `$USER ALL=(ALL) NOPASSWD: ALL` to visudo
* `apt update`
* `apt install avahi-daemon qemu-guest-agent zsh`
* `git clone git@github.com:mtrudel/dotfiles.git`
* `cd dotfiles && ./install.zsh zsh ssh snap nvim git`
* `curl -fsSL https://get.docker.com -o get-docker.sh`
* `sudo sh ./get-docker.sh`
* `sudo usermod -aG docker $USER`
* Log back in

# In operation

We set this up in a cabinet next to the TV (a Vizio P65-F1) and have it wired up
like so:

* HDMI on the Nvidia card connected to HDMI 5 (set to low latency game mode). A
  [Pulse-Eight CEC
  Adapter](https://www.pulse-eight.com/p/104/usb-hdmi-cec-adapter) is connected
  inline to pass CEC commands
* HDMI on the motherboard connected to HDMI 3 (for console use)
* Wired ethernet

The host OS and Linux guest OS runs 24/7, and the Windows runs on demand
when we want to game. The `run` script that gets set up in 'Windows Guest
Install' allows us to turn on the Windows machines by 'mashing Control+C a few times
and then typing r-u-n enter' on the keyboard (this actually works really well in
practice and is super accessible for family members). CEC takes care of turning
on the TV and switching the input, and within 30s or so you're looking at a
freshly booted Windows desktop. When done, you just shut down the Windows OS
normally. The qemu hook script doesn't seem to run reliably in this situation,
which is why we set up a crontab to run every two minutes. Once this fires, the
machine will switch back to low-power mode, ready for the next gaming session.

## Power consumption

In low power mode (ie: when the Windows guest is not running), this setup pulls
an average of 23-24W as measured at the wall, and when at peak gaming it can get
up to 400W or more.

I don't really care too much about power usage while gaming; that's a
time-limited activity and basically par for the course. In terms of efficiency
in low power mode, there's one loose end that I'd love to resolve: Nvidia recently
added support for [runtime D3 power saving](https://download.nvidia.com/XFree86/Linux-x86_64/545.23.06/README/dynamicpowermanagement.html),
but it's dependent on the BIOS exposing `_PR{0,3}` and `_PS{0,3}` ACPI methods,
which this motherboard does not implement. I've doctored up a version of the
driver with some extra logging and verified that this is in fact the limiting
factor

## Monitoring

TBD. I've got some nice Grafana dashboards for this that I should talk about

## Maintenance Tasks

### Fixing CEC

CEC's physical address detection is super flaky and will read its physical input from the i915
if it's plugged, even if the dongle is plugged in elsewhere (this shows up as 'reading drm' in
the logs). This will cause errors in our setup because the Intel GPU is plugged
in to the TV (for console access), and so cec-client will think that that's the
port it should be using.

* Get around this by temporarily disconnecting the Intel GPU and running any
  cec-client command with `-p 5` (where 5 is the HDMI input).
* This will save this physical address to EEPROM, which you can subsequently force by using `-r`
* When in doubt, [cec-o-matic](https://www.cec-o-matic.com) is great

### Kernel updates

When upgrading the kernel, take care to also install the matching
`proxmox-headers-x.y.z-pve` package to allow the Nvidia driver to stay up to
date via DKMS. If things somehow don't work, you can fix it via:

* `apt purge *nvidia*`
* `apt autoremove`
* `apt clean`
* `apt install proxmox-headers-6.11.0-1-pve` (or whatever new version is)
* Re-run the Nvidia install section above
