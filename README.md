# Rabble

Rabble is our home server / gaming PC. My goal was to have a machine that could
take over the burden of running the [various
things](https://github.com/mtrudel/pibox) we run around the house, and also to
act as a couch gaming PC with enough oomph to play any game we'd like. Some stuff about it:

* It runs CachyOS more or less out of the box (specific customization
  instructions are below). This hosts all of our Steam games without issue.
* It runs a bunch of docker containers that are described at my
  [pibox](https://github.com/mtrudel/pibox) project
* It used to run multiple VMs on a [Proxmox](https://www.proxmox.com/) host. See
  the git history of this repo if you're curious about the docs for that setup
* We have it set up for couch gaming, with some extra provision for
  auto-switching the TV and optimized power consumption when the video output is
  off (which is most of the time)
* It's Animal Crossing themed! When we were putting together the [part
  list](https://ca.pcpartpicker.com/b/nVJfrH), we
  noticed that the palette looked a lot like the colours in ACNH, so we doubled down
  with some fun decorating (more below) and named it after our family island ('rabble')

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

## Decorating

We designed the Nook print vinyl sticker & had it printed at StickerYou. The Tom
Nook figurine is an Amiibo. We also bought a [couple of light
bars](https://www.aliexpress.com/item/1005005989319012.html) from AliExpress, and
after some failed experiments trying to control them in software, I picked up a
[standalone RGB controller](https://www.aliexpress.com/item/1005007513322954.html)
that is powered directly off the PSU and is stuck on the bottom of the case for
the rare time that we actually want to have the RGB lighting on.

## BIOS

As this build is vulnerable to Intel's recent [CPU self-destruct
bug](https://www.pcmag.com/explainers/intels-raptor-lake-desktop-cpu-bug-what-to-know-what-to-do-now),
the first thing we did at first boot was to update the BIOS to the latest
version which is supposedly safe.

It's currently running the following BIOS settings (notes are somewhat terse but
you can figure it out):

* Reset factory defaults
* Ai Tweaker
  * Intel Adaptive Boost Technology to Enabled
* Advanced / Platform Misc Configuration
  * Native ASPM to Enabled
  * DMI Link ASPM Control to L1
  * ASPM to L1
  * L1 Substates to L1.1 & L1.2
  * DMI ASPM to ASPM L1
  * DMI Gen3 ASPM to ASPM L1
  * PEG - ASPM to L0sL1
* Advanced / Platform Misc Configuration / CPU - Power Management Control
  * CPU C-states to Enabled
  * Package C State Limit to C10
* Advanced / SA Configuration
  * Enable VMD Controller to Disabled
* Advanced / PCH Storage Configuration
  * Aggressive LPM Support to Enabled
* Advanced / APM Configuration
  * Restore AC Power Loss to Last State
* Advanced / Thermal Configuration
  * Intel Dynamic Tuning Technology to Enabled
* Advanced / Onboard Devices Configuration
  * HD Audio to Disabled
  * Wifi/Bluetooth to Disabled
  * When system is in working State to Stealth Mode
* Monitor
  * CPU Temperature LED Switch to Disabled
  * CPU fan:
    * Step up/down to Level 1
  * Chassis fan (top fan):
    * Mode to Manual
    * Step up/down to Level 2
    * Values to 70 100 60 60 50 40 40 0 (may not go to 0, try after a reboot)
  * AIO fan (bottom & back fan):
    * Mode to Manual
    * Step up/down to Level 3
    * Pump Speed Lower Limit to 200 RPM
    * Values to 70 60 60 40 50 20 40 0 (may not go to 0, try after a reboot)
* Advanced / Trusted Computing
  * Security Device Support to Disable
* Boot / Boot Configuration
  * Wait for F1 If Error to Disable
  * Setup Mode to Advanced Mode
* Security
  * UEFI Variable Protection / Password Protection of Runtime Variables to Disable

Many of these can optionally be managed in Linux, see the [EFI Notes](efi.md) for details

## Burn In / Benchmarking

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

# Base OS Install

* Before starting, ensure that the router has a static DHCP lease for this machine to x.y.z.2
* Download the latest CachyOS ISO and flash it to a USB drive using Balena Etcher or similar
* Boot into the installer, selecting defaults along the way for everything except disk partitioning, which are:
    * GPT partition table
    * 8192MB FAT32, mounted at /boot, flags 'boot'
    * Remainder btrfs, mounted at /, no flags
* Reboot into the newly installed OS
* Disable the 'Start Automatically' toggle in the bottom of the welcome window
* Go into the settings app, change:
    * Sound: Set HDMI output to Digital Surround 5.1
    * Display: Set scale to 250%
    * Display: Adaptive Sync to Automatic
    * Display: Enable HDR (and calibrate)
    * Firewall: Disable
    * Login Screen: Automatically log in as user
    * Screen Locking: Set to Never
    * Screen Locking: Disable lock on wake from sleep
    * Power Management: When Inactive: Do Nothing
    * Power Management: When Power Button Pressed: Turn Off Screen
    * Power Management: Dim Automatically: Never
    * Power Management: Turn off screen: After 5 minutes
    * Power Management: Switch to power profile: Power Save
    * Power Management: When Inactive: 5 minutes
    * Autostart: Delete CachyOS Hello (if present)
* Open up Alacritty and run:
    * `sudo systemctl enable --now sshd`
* Copy ssh key to new machine: `ssh-copy-id rabble.local`
* ssh to `rabble.local` and:
    * Customize basic system stuff:
        * `echo 'PasswordAuthentication no' > /etc/ssh/sshd_config.d/99-local.conf`
        * `echo 'mat ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/99-local`
    * Install docker:
        * `sudo pacman -S docker docker-compose`
        * `sudo systemctl enable --now docker`
        * `sudo usermod -aG docker $USER` (Log out and back in to get docker permissions)
    * Install Steam:
        * `sudo pacman -S cachyos-gaming-meta steam`
* In the GUI:
    * Log into Steam
    * In Steam settings, Interface:
        * Enable 'Run Steam when my computer starts'
        * Enable 'Start Steam in Big Picture Mode'
        * Enable 'Enable CPU accelerated rendering in web views'
    * Reboot the system and ensure it comes up cleanly into Steam

### Set up my dotfiles

* `sudo pacman -S neovim` (pick the default providers for deps)
* `chsh` (select `/bin/zsh`)
* `git clone git@github.com:mtrudel/dotfiles.git`
* `cd dotfiles && ./install.zsh git nvim ssh zsh`

# In operation

We set this up in a cabinet next to the TV (an LG OLED77B5PUA) and have it wired
up like so:

* HDMI on the Nvidia card connected to any input on TV (it should auto-set to
  low latency game mode)
* Wired ethernet
* The TV is connected to wifi, but blocked at the router to avoid phoning home.
    * 'IP Control' and 'Wake on LAN' need to be enabled on the TV for the auto
      on/off to work (discussed in 'gaming conveniences', below)

## Gaming conveniences

* Boot to a bare console by default instead of straight into the GUI (saves ~400MiB
  VRAM vs. a running compositor):
    * `sudo systemctl set-default multi-user.target`
* Wake to the GUI when an 8BitDo controller powers on (the controllers change their USB product ID when they wake up, from `2dc8:301c` to `2dc8:310a`). Handles two cases: bringing the whole session up from a bare console, or just waking an already-running session whose screen has gone DPMS-blank from idle
    ```bash
    sudo tee /etc/udev/rules.d/99-8bitdo-tv.rules <<EOF
    ACTION=="add", SUBSYSTEM=="hidraw", ATTRS{idVendor}=="2dc8", ATTRS{idProduct}=="310a", RUN+="/usr/bin/systemctl --no-block start 8bitdo-gui-wake.service"
    EOF
    sudo tee /etc/systemd/system/8bitdo-gui-wake.service <<EOF
    [Unit]
    Description=Switch to graphical session when 8BitDo controller connects

    [Service]
    Type=oneshot
    ExecStart=/usr/bin/touch /run/switch-session-pending
    ExecStart=/usr/bin/systemctl isolate graphical.target
    ExecStart=-/usr/bin/runuser -u mat -- /bin/bash -c 'XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 kscreen-doctor --dpms on'
    ExecStart=-/usr/local/bin/tv-ctl on
    EOF
    sudo systemctl daemon-reload && sudo udevadm control --reload-rules
    ```
    The controller-wake and the PowerDevil idle-triggered auto-suspend (`isolate
    multi-user.target`, see below) can fire in opposite directions at nearly the
    same instant. `isolate` stops *everything* not required by its destination
    target so either one can kill the other as pure collateral. The `touch`
    above is fast enough to complete before any kill, and
    `session-switch-resume.service` below picks up the marker and finishes the
    job once the race resolves.
    ```bash
    sudo tee /etc/systemd/system/session-switch-resume.service <<EOF
    [Unit]
    Description=Resume to graphical.target after a manual session switch or a lost isolate race
    ConditionPathExists=/run/switch-session-pending
    After=multi-user.target

    [Service]
    Type=oneshot
    ExecStart=/bin/sh -c 'rm -f /run/switch-session-pending; systemctl isolate graphical.target'
    ExecStart=-/usr/bin/runuser -u mat -- /bin/bash -c 'XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 kscreen-doctor --dpms on'
    ExecStart=-/usr/local/bin/tv-ctl on

    [Install]
    WantedBy=multi-user.target
    EOF
    sudo systemctl daemon-reload && sudo systemctl enable session-switch-resume.service
    ```
    Screen dims after `TurnOffDisplayIdleTimeoutSec` (in `~/.config/powerdevilrc`)
    If the screen isn't blanking on schedule, `systemctl --user restart
    plasma-powerdevil.service` fixes it.
* Make "Suspend" (Steam Big Picture, Plasma power menu) drop to the bare console
  instead of actually suspending the machine, by overriding
  `systemd-suspend.service`'s `ExecStart` (wrapped in `systemd-run --no-block` since
  isolating directly from within the unit that's running conflicts with itself):
    ```bash
    sudo mkdir -p /etc/systemd/system/systemd-suspend.service.d
    sudo tee /etc/systemd/system/systemd-suspend.service.d/99-drop-graphical-instead.conf <<EOF
    [Service]
    ExecStart=
    ExecStart=/usr/bin/systemd-run --no-block --collect /usr/bin/systemctl isolate multi-user.target
    EOF
    sudo systemctl daemon-reload
    ```
* TV on/off/input/volume control via LG's SSAP protocol spoken directly with
  [`tv-ctl`](tv-ctl) over `websocat`/`jq`/`wakeonlan` to keep this simple and
  dependency free:
    * `sudo pacman -S websocat jq wakeonlan`
    * `sudo mkdir -p /etc/rabble-tv && sudo cp lgtv-manifest.json /etc/rabble-tv/manifest.json`
      ([lgtv-manifest.json](lgtv-manifest.json) is the standard, publicly-reused LG
      pairing manifest - the same `com.lge.test` blob bscpylgtv/lgtv2/etc. all use)
    * `sudo install -m 755 tv-ctl /usr/local/bin/tv-ctl`
    * `sudo mkdir -p /var/lib/rabble-tv && sudo chown mat:mat /var/lib/rabble-tv`
    * `tv-ctl register` once (TV must be on; accept the prompt on-screen within 45s)
      to populate `/var/lib/rabble-tv/client-key`
    * `audio/setVolume` only updates the TV's own internal counter and does nothing
      audible once sound is routed to an external soundbar over ARC/eARC - `tv-ctl`
      instead tracks its own last-known level in `/var/lib/rabble-tv/volume` and
      steps to the target via the same relative `volumeUp`/`volumeDown` calls the
      physical remote's rocker uses
    * every call retries for ~12s: `logind` broadcasts `PrepareForSleep` on any
      suspend (including the fake one above) outside the systemd unit graph, so
      NetworkManager briefly drops networking right when `tv-ctl` needs it
* Tie the TV state to entering/leaving the GUI (rather than an idle timer) via a service
  hung directly off `graphical.target`:
    ```bash
    sudo tee /etc/systemd/system/tv-gui-hook.service <<EOF
    [Unit]
    Description=Turn TV on/off in sync with entering/leaving the graphical session

    [Service]
    Type=oneshot
    RemainAfterExit=yes
    TimeoutStopSec=30
    ExecStart=/usr/local/bin/tv-ctl on
    ExecStop=/usr/local/bin/tv-ctl off

    [Install]
    WantedBy=graphical.target
    EOF
    sudo systemctl daemon-reload && sudo systemctl enable --now tv-gui-hook.service
    ```
    (`TimeoutStopSec=30` overrides this box's unusually short 10s default stop
    timeout, giving `tv-ctl`'s retries above room to actually finish)

## Idle power consumption

In low power mode (ie: when the display is not running and the GPU is idle),
this setup pulls around 33-34W as measured at the wall. At peak gaming it can
get up to 400W or more. I don't really care too much about power usage while gaming; that's a
time-limited activity and basically par for the course. The far more relevant
optimizations are around consumption when the box is idle.

I measured at ~33-34W at the wall with TV plugged in but off, ethernet
connected, and USB devices as described below. Conditions: BIOS settings as
above (notably RAM settings make a big difference), LTR ignore active, EEE
enabled, all docker containers running:

| Component | Draw | Basis |
|-----------|------|-------|
| CPU core (i5-13600K idle) | 3W | RAPL (measured via turbostat on minimal system) |
| CPU package (i5-13600K idle) | 0.5W | RAPL (measured via turbostat on minimal system) |
| GPU (RTX 4070, deep idle) | 3.4W | nvidia-smi (measured) |
| DDR5-4800 2×stick @ 1.1V | 3W | measured by booting with one stick removed |
| USB devices | 2W | measured with USB current meter |
| Fans (3× slow: 341/559/503 RPM) | 0.5W | estimated from spec sheets |
| NVMe SSD (P41 in APST PS4) | 0.5W | estimated from PS4 residency |
| Ethernet (I226-V + EEE) | 1W | measured on base system |
| Additional CPU / Core load from docker | 5W | measured compared to minimal system |
| PSU losses (~82% @ 4.4% load of 18.9W) | 4.2W | Cybenetics RM750e report + low-load penalty |
| **Total** | **~23W** | observed gap of 10W compared to 33W wall measurement |

There is a gap of approximately 10-11W between the sum of the components
and the observed power draw at the wall. Approximately 6W of that is directly
related to the GSP firmware structure of the open drivers (reverting to an
earlier version of the proprietary driver & disabling GSP brings the idle value
down by 6W). This is a known issue with the open drivers and is unavoidable. The
remainder of the gap (4-5W) is unaccounted for, but seems related to the GPU
being present. Physically removing the card reduces power consumption to a level
that is entirely explained by the items in the above table. This is apparently an
issue with consumer RTX cards that the reported power usage in nvidia-smi only
includes the GPU itself, and does not account for both the increase due to GSP
firmware use, but also GDDR refreshing, VRMs or other components on the GPU.

The tl;dr here is that running the GPU on an up to date driver unavoidably
consumes an additional 13-14W of power at idle, even though nvidia-smi is only
reporting 3-4W of use. I've spent a LOT of effort trying to reduce this by
having the card drop into D3Cold when idle, but since the motherboard does not
support physically cutting the power rail to the GPU slot, this ends up
consuming quite a bit MORE power than the current setup. See the
[gpu.md](gpu.md) research log for more info.

### Power Tweaks

The box has a few teaks in place to help optimize power consumption at idle:

* Ignore latency requests for a number of devices (improves C-state residency for the CPU package, good for about 1.5W):
  ```bash
  sudo tee /etc/systemd/system/pmc-ltr-ignore.service <<EOF
  [Unit]
  Description=Ignore PMC LTR entries to allow deeper package C-states
  After=local-fs.target

  [Service]
  Type=oneshot
  ExecStart=/bin/sh -c "echo 0 > /sys/kernel/debug/pmc_core/ltr_ignore"
  ExecStart=/bin/sh -c "echo 4 > /sys/kernel/debug/pmc_core/ltr_ignore"
  ExecStart=/bin/sh -c "echo 6 > /sys/kernel/debug/pmc_core/ltr_ignore"
  RemainAfterExit=yes

  [Install]
  WantedBy=multi-user.target
  EOF
  sudo systemctl enable --now pmc-ltr-ignore.service
  ```
* Enable EEE mode on the ethernet port (good for about 0.5W):
  ```bash
  sudo tee /etc/NetworkManager/dispatcher.d/99-eee <<EOF
  #!/bin/bash
  IFACE="$1"
  ACTION="$2"

  if [[ "$IFACE" == "enp5s0" && "$ACTION" == "up" ]]; then
      ethtool --set-eee enp5s0 eee on
  fi
  EOF
  sudo chmod +x /etc/NetworkManager/dispatcher.d/99-eee
  ```
* Auto-suspend unused USB devices (good for 0.2W):
  ```bash
  sudo tee /etc/udev/rules.d/99-aura-autosuspend.rules <<EOF
  ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="0b05", ATTR{idProduct}=="19af", ATTR{power/control}="auto"
  EOF
  ```
* Start `power-profiles-daemon` on all boots (default unit only wants `graphical.target`):
  ```bash
  sudo systemctl enable power-profiles-daemon
  sudo ln -sf /usr/lib/systemd/system/power-profiles-daemon.service \
      /etc/systemd/system/multi-user.target.wants/power-profiles-daemon.service
  ```

## Monitoring

The box is monitored by our home Grafana stack (TBD: I've got some nice dashboards for this that I should talk about)

* `sudo pacman -S prometheus-node-exporter`
* `sudo systemctl enable --now prometheus-node-exporter`
* Enable RAPL power metrics (node_exporter runs as an unprivileged user and can't read `/sys/class/powercap/` by default):
  ```bash
  sudo mkdir -p /etc/systemd/system/prometheus-node-exporter.service.d
  sudo tee /etc/systemd/system/prometheus-node-exporter.service.d/rapl.conf <<EOF
  [Service]
  AmbientCapabilities=cap_dac_read_search
  EOF
  sudo systemctl daemon-reload && sudo systemctl restart prometheus-node-exporter
  ```
* `sudo sensors-detect` (accept all the defaults)

# Research projects

* [GPU power saving notes](gpu.md) (mostly Claude maintained)
* [EFI variable snapshotting](efi.md) (mostly Claude maintained)
