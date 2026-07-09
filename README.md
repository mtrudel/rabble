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
  with some fun decorating (more below), named it after our family island ('rabble')

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
    * Step up.down to Level 2
    * Values to 70 100 60 60 50 40 40 0 (may not go to 0, try after a reboot)`
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

# OS Install

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
        * `sudo pacman -S nvme-cli`
        * `sudo pacman -S turbostat`
    * Install docker:
        * `sudo pacman -S docker docker-compose`
        * `sudo systemctl enable --now docker`
        * `sudo usermod -aG docker $USER` (Log out and back in to get docker permissions) * In GUI:
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

### TV Tweaks

This installs tools to help with turning the TV on and off when the display goes
to sleep

TBD - working on this currently

# In operation

We set this up in a cabinet next to the TV (an LG OLED77B5PUA) and have it wired up
like so:

* HDMI on the Nvidia card connected to any input on TV (it should auto-set to
low latency game mode)
* Wired ethernet
* The TV is connected to wifi, but blocked at the router to avoid phoning home.
    * 'IP Control' and 'Wake on LAN' need to be enabled on the TV for the above
      hooks to work

## Power consumption

In low power mode (ie: when the display is not running and the GPU is idle),
this setup pulls around 30-35W as measured at the wall. At peak gaming it can
get up to 400W or more.

I don't really care too much about power usage while gaming; that's a
time-limited activity and basically par for the course. The far more relevant
optimizations are around consumption when the box is idle. The theoretical
minimum (GPU in D3cold, CPU in PC10) is probably closer to 23-24W, but achieving
that requires a bunch of stars to align, some of which seem unsolvable. See the
following section for the work done to date

### Idle power budget

Measured at ~33-34W at the wall with TV plugged in but off, ethernet connected,
and USB devices as described below. Conditions: BIOS settings as above (notably
RAM settings make a big difference), LTR ignore active, EEE enabled.

| Component | Draw | Basis |
|-----------|------|-------|
| CPU core (i5-13600K idle) | 3W | RAPL (measured via turbostat on minimal
system) |
| CPU package (i5-13600K idle) | 0.5W | RAPL (measured via turbostat on minimal
system) |
| GPU (RTX 4070, deep idle) | 3.4W | nvidia-smi (measured) |
| DDR5-4800 2×stick @ 1.1V | 3W | meaured by booting with one stick removed |
| USB devices | 2W | measured with USB current meter |
| Fans (3× slow: 341/559/503 RPM) | 0.5W | estimated from spec sheets |
| NVMe SSD (P41 in APST PS4) | 0.5W | estimated from PS4 residency |
| Ethernet (I226-V + EEE) | 1W | measured on base system |
| Additional CPU / Core load from docker | 5W | measured compared to minimal system |
| PSU losses (~82% @ 4.4% load of 18.9W) | 4.2W | Cybenetics RM750e report + low-load penalty |
| **Total** | **~23W** | observed gap of 10W compared to 33W wall measurement |

There is an gap of approximately 10-11W between the sum of the components
and the observed power draw at the wall. This gap has been narrowed specifically
to the presence of the GPU by a process of elimination. It is apparently a known
issue with consumer RTX cards that the reported power usage in nvidia-smi only
includes the GPU itself, and does not account for GDDR refreshing, VRMs or other
components on the GPU.

## Power management active work

### Nvidia Runtime D3 (RTD3)

The Nvidia driver supposedly supports runtime D3 power management, which allows
the GPU to enter low-power states when idle. However, the fine-grained RTD3 mode
also requires the BIOS to expose `_PR3` ACPI power resource methods on the GPU's
PCIe device node. Rabble's motherboard doesn't provide this so the driver falls
back to "Not supported" without intervention.

The Claude-assisted fix is an ACPI SSDT override that injects the missing `_PR3`
methods. The source is `nvidia-d3.dsl` in this repo. To rebuild the `.aml`
binary from it:

```bash
# Install iasl if needed: sudo pacman -S acpica
iasl -sa nvidia-d3.dsl    # produces nvidia-d3.aml
```

The `.dsl` file adds a stub `PowerResource` (PGPR) to the GPU's PCIe root port
(`\_SB.PC00.PEG1`) and attaches it as `_PR3` on both the root port and the GPU
endpoint (`\_SB.PC00.PEG1.PEGP`).

A second SSDT, `nvidia-s0ix.dsl`, patches the Intel Platform Energy Policy
device (PEPD / `INT33A1`) to set the `S0ID` flag to 1 at boot. The BIOS leaves
this at 0 on desktop boards, which causes PEPD's `_DSM` function 1 to return
an empty device constraint list, preventing the kernel's LPS0 path from
coordinating low-power S0 idle device entry. Setting `S0ID=1` enables that
constraint list. Build it the same way: `iasl -sa nvidia-s0ix.dsl`.

### Installing the SSDT overrides

The compiled `.aml` files need to be bundled into the initramfs so the kernel
loads them at boot. The cleanest way on CachyOS (mkinitcpio):

1. Copy the AML files to a persistent location:
   ```bash
   sudo mkdir -p /etc/acpi/override
   sudo cp nvidia-d3.aml nvidia-s0ix.aml /etc/acpi/override/
   ```

2. Create `/etc/initcpio/install/acpi_override`:
   ```bash
   #!/usr/bin/env bash
   build() {
       local aml dest
       for aml in /etc/acpi/override/*.aml; do
           [[ -f "$aml" ]] || continue
           dest="$EARLYROOT/kernel/firmware/acpi/${aml##*/}"
           mkdir -p "${dest%/*}"
           cp "$aml" "$dest"
       done
   }
   ```
   The hook writes to `$EARLYROOT` (not `$BUILDROOT`) so the AML lands in the
   early uncompressed CPIO section — the kernel only scans that section for ACPI
   overrides, not the main compressed image.

3. Add `acpi_override` to the `HOOKS` array in `/etc/mkinitcpio.conf` (before
   `filesystems`).

4. Rebuild the initramfs:
   ```bash
   sudo mkinitcpio -P
   ```

After rebooting, verify it loaded:
```bash
dmesg | grep -i 'ACPI.*SSDT.*NVIDIA'
cat /proc/driver/nvidia/gpus/*/power | grep 'Runtime D3'
# should show: Runtime D3 status: Enabled (fine-grained)
```

**BUT** it should be noted that none of the above move the needle on power
consumption as measured at the wall. It seems that the GPU is pretty good at
managing its own power consumption without the above (as measured by `nvidia-smi -q -d POWER`), and it's also not enough to get the CPU package C states below C2.

This change has since been backed out

### Audio power management

Add `snd_hda_intel.power_save=1` to the `KERNEL_CMDLINE` line in `/etc/default/limine`.
This takes effect automatically on the next kernel update. To apply it immediately
to existing entries, also edit the `cmdline:` lines directly in `/boot/limine.conf`.

Also mask the system udev rule that overrides this on AC power (designed for
laptops to prevent audio crackling; not relevant on a desktop with no battery):
```bash
sudo touch /etc/udev/rules.d/20-audio-pm.rules
```

After rebooting, verify with:
```bash
cat /sys/module/snd_hda_intel/parameters/power_save  # should show 1
```

**AGAIN** this seems to have negligible effect at the wall

This change has since been backed out

### NVMe power management

The NVMe drive's `power/control` attribute defaults to `on`, so a udev rule is needed to enable autosuspend

```bash
echo 'ACTION=="add", SUBSYSTEM=="pci", ATTR{class}=="0x010802", ATTR{power/control}="auto"' \
    | sudo tee /etc/udev/rules.d/99-nvme-autosuspend.rules
```

**AGAIN** this seems to have negligible effect at the wall

This change has since been backed out

### AURA LED Controller USB autosuspend

The ASUS AURA LED Controller (used for motherboard RGB) is a USB device that stays
active by default even though we don't use it (RGB is driven by a standalone hardware
controller instead). A udev rule suspends it automatically:

```bash
echo 'ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="0b05", ATTR{idProduct}=="19af", ATTR{power/control}="auto"' \
    | sudo tee /etc/udev/rules.d/99-aura-autosuspend.rules
```

The device suspends within a few seconds of boot and stays suspended. Minor power
saving on its own, but removes one always-active device from the USB controller's
wakeup load.

### PMC LTR ignore

The Intel PMC (Platform Management Controller) uses LTR (Latency Tolerance Reporting)
values advertised by platform devices to decide whether to allow deep package C-states.
On this B760 desktop board, three devices report LTR values that block the platform
from entering states below PC2 indefinitely:

- Entry 0: SOUTHPORT_A (PCIe port — the NVMe drive)
- Entry 4: XHCI (USB controller)
- Entry 6: ME (Intel Management Engine)

Ignoring these entries saves **2-3W at the wall** by allowing the platform to enter
deeper idle states. Persist via a systemd oneshot service:

Create `/etc/systemd/system/pmc-ltr-ignore.service`:
```ini
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
```

```bash
sudo systemctl enable --now pmc-ltr-ignore.service
```

Note: the IRTL MSRs (which gate PC6/PC8/PC10) are read-only on this platform — the
BIOS doesn't set them and they can't be written from the OS. PC3 flickers briefly but
PC6+ remains unachievable on this desktop B760 board regardless.

### Ethernet EEE (Energy Efficient Ethernet)

Enabling EEE on the NIC makes a measurable difference at the wall. Persist it via a NetworkManager dispatcher script so it runs whenever the interface comes up (handles reboots and suspend/resume):

Create `/etc/NetworkManager/dispatcher.d/99-eee`:
```bash
#!/bin/bash
IFACE="$1"
ACTION="$2"

if [[ "$IFACE" == "enp5s0" && "$ACTION" == "up" ]]; then
    ethtool --set-eee enp5s0 eee on
fi
```

```bash
sudo chmod +x /etc/NetworkManager/dispatcher.d/99-eee
```

The script runs as root automatically so no `sudo` is needed inside it.

### BIOS EFI variable tweaks

The BIOS exposes many power-relevant settings that are not visible in the standard
ASUS GUI. These can be written directly to EFI variable files from Linux; the Intel
Reference Code reads them at POST time on the next boot.

The following RC-only settings were identified by cross-referencing the AMI IFR
(extracted from the BIOS flash via UEFIExtract + ifrextractor-rs) with live EFI vars,
and trialled as potential power savers:

| Variable | Offset | Default | Tried | Description |
|----------|--------|---------|-------|-------------|
| Setup | 0xCBA | 0 | 1 | Clock Power Management — gates PCIe reference clock when links idle |
| Setup | 0xCAD | 0 | 1 | Unpopulated Links — powers down empty PCIe slots |
| SaSetup | 0x37F–0x381 | 0 | 3 | PEG1–PEG3 L1 Substates → L1.1+L1.2 |
| PchSetup | 0x2C1–0x2CF | 0 | 3 | PCH root ports 2–16 L1 Substates → L1.1+L1.2 |

**These changes have since been backed out** — they caused a ~1W regression at the
wall with no measurable benefit. All offsets are now at firmware defaults.

Note: writing EFI variables from Linux requires removing the immutable flag temporarily
(`chattr -i`). The restore script handles this automatically. A wrong offset could
corrupt a setting (recoverable via BIOS "Load Defaults"), but does not risk bricking.

### BIOS snapshot / restore

`bios_snapshot.json` contains all GUI-visible settings that differ from their
IFR factory defaults.

To diff current state against the snapshot:

```bash
sudo python3 restore_bios.py
```

To restore everything after a CMOS reset or reflash:

```bash
sudo python3 restore_bios.py --apply
# then reboot
```

To regenerate `bios_snapshot.json` after making intentional BIOS changes (run on
rabble as root):

```bash
sudo python3 capture_bios.py
```

The capture script parses the AMI IFR extracted from the live BIOS flash, compares
every GUI-settable question against its factory default, and records all differences.
The IFR is cached in `/tmp` and re-extracted automatically when missing (e.g. after
a reboot) or on demand with `--regen-ifr`.

## Monitoring

TBD. I've got some nice Grafana dashboards for this that I should talk about
