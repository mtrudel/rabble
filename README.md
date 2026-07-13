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

This wires up automatic TV power control: the TV turns off after 5 minutes of
inactivity and wakes (via WoL + input switch to HDMI 2) when activity resumes.
The TV must have **IP Control** and **Wake on LAN** enabled in its network
settings (Quick Start+ is not required).

Install the tools:
```bash
sudo pacman -S python-pip wakeonlan swayidle
python3 -m pip install bscpylgtv --user --break-system-packages
```

Pair with the TV (TV must be on; accept the prompt that appears on screen):
```bash
WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 ~/.local/bin/bscpylgtvcommand 192.168.10.172 get_system_info
```

This stores a key in `~/.local/share/bscpylgtv/` and only needs to be done once.

Create `~/.local/bin/tv-off.sh`:
```bash
#!/bin/bash
/home/mat/.local/bin/bscpylgtvcommand 192.168.10.172 power_off
```

Create `~/.local/bin/tv-on.sh`:
```bash
#!/bin/bash
/usr/bin/wakeonlan f4:14:bf:56:99:9a
sleep 8
/home/mat/.local/bin/bscpylgtvcommand 192.168.10.172 set_input HDMI_2
```

```bash
chmod +x ~/.local/bin/tv-{on,off}.sh
```

Hook them into Plasma's idle events via swayidle (which works on any Wayland
compositor via the idle protocol). Create
`~/.config/systemd/user/tv-screen-watch.service`:
```ini
[Unit]
Description=TV power control via swayidle screen events
After=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/bin/swayidle -w \
    timeout 300 '/home/mat/.local/bin/tv-off.sh' \
    resume '/home/mat/.local/bin/tv-on.sh'
Restart=on-failure
RestartSec=5

[Install]
WantedBy=graphical-session.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now tv-screen-watch.service
```

#### 8BitDo controller wake

The 8BitDo 2.4GHz controllers (vendor `2dc8`) switch from an IDLE product ID
(`301c`) to an active one (`310a`) when powered on. A udev rule catches this and
wakes both the KDE display and the TV.

Install ydotool (needed to generate a kernel-level input event that wakes KWin's
DPMS — `org.freedesktop.ScreenSaver.SimulateUserActivity` doesn't work since
kscreenlocker isn't running when screen locking is disabled):
```bash
sudo pacman -S ydotool
systemctl --user enable --now ydotool.service
```

Create `/etc/udev/rules.d/99-8bitdo-tv.rules`:
```
ACTION=="add", SUBSYSTEM=="hidraw", ATTRS{idVendor}=="2dc8", ATTRS{idProduct}=="310a", RUN+="/usr/bin/systemctl --no-block start 8bitdo-tv-on.service"
```

Create `/etc/systemd/system/8bitdo-tv-on.service`:
```ini
[Unit]
Description=Wake TV when 8BitDo controller connects

[Service]
Type=oneshot
ExecStart=/usr/bin/runuser -u mat -- /bin/bash -c '\
    YDOTOOL_SOCKET=/run/user/1000/.ydotool_socket \
    /usr/bin/ydotool key 57; \
    /home/mat/.local/bin/tv-on.sh'
Environment=HOME=/home/mat
```

```bash
sudo systemctl daemon-reload
sudo udevadm control --reload-rules
```

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

Nvidia fine-grained RTD3 allows the GPU to enter D3cold (near-zero power) when
idle. Three things must be in place together:

1. **ACPI `_PR3` power resource on PEG1** — the BIOS doesn't provide this, so an
   SSDT override injects it. The source is `nvidia-d3.dsl` in this repo:
   ```bash
   # Install iasl if needed: sudo pacman -S acpica
   iasl -sa nvidia-d3.dsl    # produces nvidia-d3.aml
   ```
   The DSL adds a stub `PowerResource` (PGPR) to the GPU's PCIe root port
   (`\_SB.PC00.PEG1`) and attaches it as `_PR3` on both the root port and the GPU
   endpoint (`\_SB.PC00.PEG1.PEGP`).

2. **BIOS EFI variable tweaks** (see section below) — `ACPI D3Cold Support` and
   `PEG L1 Substates` must be enabled for the PCIe link to reach the deep idle
   state RTD3 depends on.

3. **Nvidia module parameter** — the driver's S0ix/RTD3 path must be armed:
   ```bash
   echo 'options nvidia NVreg_EnableS0ixPowerManagement=1' \
       | sudo tee /etc/modprobe.d/nvidia-power.conf
   sudo mkinitcpio -P
   ```

### Installing the SSDT override

The compiled `.aml` needs to be bundled into the initramfs so the kernel loads it
at boot:

1. Copy the AML to a persistent location:
   ```bash
   sudo mkdir -p /etc/acpi/override
   sudo cp nvidia-d3.aml /etc/acpi/override/
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

After rebooting, verify:
```bash
sudo dmesg | grep -i 'SSDT.*NVIDIA'         # confirms AML loaded from initramfs
cat /proc/driver/nvidia/gpus/*/power         # Runtime D3 status: Enabled (fine-grained)
                                             # S0ix Platform Support: Supported
```

RTD3 only activates when the GPU is truly idle (no compositor VRAM above 200 MiB).
In practice this means the display must be off and kwin must have released GPU
resources. Check with:
```bash
cat /sys/bus/pci/devices/0000:01:00.0/power_state   # D3cold when idle
```

Note: S0ix `Status` remains `Disabled` due to a persistent ASUS BIOS bug
(`_DSM.USRG AE_ALREADY_EXISTS` on `\_SB.PC00.PEG1.PEGP`) that aborts the
Nvidia driver's GPU-side S0ix capability check. S0ix `Platform Support` is
`Supported` (fixed via EFI var), but the driver can't confirm GPU participation
until ASUS fixes the DSDT. RTD3 fine-grained works independently of this.

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

The following RC-only settings are written to EFI vars at each restore. They have no
ASUS GUI equivalent and were identified by cross-referencing the AMI IFR (extracted
from the BIOS flash via UEFIExtract + ifrextractor-rs) with live EFI vars.

| Variable | Offset | Default | Set to | Description |
|----------|--------|---------|--------|-------------|
| Setup | 0x5E | 0 | 1 | Low Power S0 Idle Capability — hidden master switch; tells Intel RC to set the ACPI S0ID flag natively (replaces the backed-out `nvidia-s0ix.dsl` SSDT approach) |
| Setup | 0x722 | 0 | 1 | ACPI D3Cold Support — hidden master switch; tells Intel RC to generate `_PR3` power resources in ACPI tables, enabling RTD3 for discrete GPU |
| SaSetup | 0x37F–0x381 | 0 | 3 | PEG1–PEG3 L1 Substates → L1.1+L1.2 — required for PCIe link to enter the deep idle state that RTD3 depends on |

Previously tried and backed out (caused ~1W regression with no benefit when D3Cold
support was not enabled):

| Variable | Offset | Default | Tried | Description |
|----------|--------|---------|-------|-------------|
| Setup | 0xCBA | 0 | 1 | Clock Power Management — gates PCIe reference clock when links idle |
| Setup | 0xCAD | 0 | 1 | Unpopulated Links — powers down empty PCIe slots |
| PchSetup | 0x2C1–0x2CF | 0 | 3 | PCH root ports 2–16 L1 Substates → L1.1+L1.2 |

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
The IFR is cached in `~/ami_setup.bin` (survives reboots) and re-extracted
automatically when missing or on demand with `--regen-ifr`.

## Big Picture wake/sleep lifecycle (planning)

Design notes for replacing today's ad hoc idle handling (swayidle → `tv-off.sh`/`tv-on.sh`
only, plus the `ydotool`-based 8BitDo wake) with `systemctl isolate` switching between
`multi-user.target` and `graphical.target` as the core mechanism. The big motivation:
`multi-user.target` measures ~34 MiB VRAM (no compositor at all) vs. ~438 MiB under
KWin — a much bigger lever on the RTD3/D3cold problem (see above) than anything
compositor-side, and it unifies wake/sleep handling across every trigger (controller,
keyboard, Steam's suspend button, Plasma's power menu) instead of each needing its own
mechanism. Assumes we stay on Plasma/KWin rather than move to a gamescope-only session
(see distro/session discussion — deferred, not decided) since a gamescope session
blurs the graphical.target boundary (Steam *is* the session there).

Nothing below is built yet except where noted.

### Improve wakeup experience

* **Controller wake** — already exists (`8BitDo controller wake` section above): udev
  rule on the hidraw product-ID change (`301c` idle → `310a` active). Currently fires
  `ydotool key 57` (the flaky synthetic keypress) — swap this for
  `systemctl isolate graphical.target` directly once target-switching exists.
* **Keyboard wake** — needs a new mechanism, not a udev rule. Whether the Keychron K3's
  2.4GHz dongle re-enumerates on sleep/wake like the controller does is unconfirmed
  (check with `udevadm monitor --subsystem-match=hidraw --subsystem-match=usb` before
  assuming either way — likely it doesn't, since that seems to be an 8BitDo-specific
  behaviour). Most likely needs a small persistent evdev watcher (`python-evdev`), run
  as a root systemd service `WantedBy=multi-user.target`, watching the keyboard's
  `/dev/input/by-id/...` path and filtering to specific keycodes only (e.g.
  `KEY_ENTER`/`KEY_SPACE`) to avoid accidental wakeups from incidental contact.
* Both paths converge on the same action: `systemctl isolate graphical.target`.

### Intercept suspend, kill graphical instead

Steam's Big Picture "Suspend", Plasma's power menu, and (if it exists) a hardware sleep
key on the keyboard all ultimately go through the same
`org.freedesktop.login1.Manager.Suspend()` → `systemd-suspend.service` path. Plan:
override that unit's `ExecStart` (`systemctl edit systemd-suspend.service`) to run
`systemctl isolate multi-user.target` instead of an actual kernel suspend, so "suspend"
uniformly means "tear down the GUI" regardless of what triggered it — no D-Bus
eavesdropping or inhibitor games needed. Open question: whether to also override
hibernate/hybrid-sleep/suspend-then-hibernate units for completeness (probably
unreachable in practice on this desktop, but cheap to do at the same time).

### Hook TV on/off to GUI start/stop

Rather than TV control living purely in swayidle's idle timeout inside the Wayland
session, tie `tv-on.sh`/`tv-off.sh` directly to entering/leaving `graphical.target` —
e.g. a oneshot service `WantedBy=graphical.target` with `ExecStart=tv-on.sh` /
`ExecStop=tv-off.sh`. The existing swayidle-based `tv-screen-watch.service` still has a
job to do for the lighter-weight "idle mid-game" case below; it doesn't get removed,
just stops being the only lever.

### Desired final outcome

* **Controller on / keypress while GUI is down** → `systemctl isolate
  graphical.target` brings everything back; the TV-on hook (tied to graphical.target
  start) turns the TV on and switches input.
* **Explicit "Suspend" in Steam** → intercepted per above, drops to multi-user.target;
  TV-off hook (tied to graphical.target stop) turns the TV off.
* **Idle timeout while a game is actively running** → don't tear down graphical.target
  (a game is running) — just let the display DPMS-off / go no-signal via the existing
  swayidle + `tv-off.sh` path, TV eventually powers itself down on its own no-signal
  handling. Lighter response than the full target-switch teardown above.
* **Loose end, not decided**: should Steam itself eventually escalate — idle in the Big
  Picture menu (no game running) for some longer period also dropping all the way to
  multi-user.target, rather than just screen-blanking? Same "is a game actually
  running" guard as elsewhere (`pgrep -f 'reaper SteamLaunch'`), just reframed as a
  possible third tier between "DPMS blank" and "full target switch."

### Other open items

* Whether the K3 has a dedicated hardware sleep key at all — its Fn row looks fully
  occupied by brightness/media/volume in Keychron's docs, no sleep icon found. Check
  the physical keycaps, or confirm with `evtest`.
* If it does, whether logind actually treats it as a power key (needs the udev
  `power-switch` tag) — check via `journalctl -u systemd-logind -f` while pressing it.
* Worth ruling out separately: `steamwebhelper`'s GPU-accelerated web-view rendering as
  a source of idle GPU activity that could block D3cold regardless of any of the above
  (Settings → Interface → disable "GPU accelerated rendering in web views" — note
  Valve bug steam-for-linux#11987 where the toggle doesn't always stick).

## Monitoring

TBD. I've got some nice Grafana dashboards for this that I should talk about
