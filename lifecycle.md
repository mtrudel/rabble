# Gaming Conveniences

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

### 8BitDo controller wake

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

Note that at some point we'll need to figure out about making
/etc/modprobe.d/nvidia-drm-fbdev.conf look like:

```
options nvidia_drm fbdev=0
```

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
