### Nvidia Runtime D3 (RTD3) — investigated, reproduced twice, not enabled

RTD3 works on rabble — both D3hot and real hardware-confirmed D3cold — but costs more
power than leaving the GPU alone. Confirmed via controlled A/B, twice (2026-07-12 and
2026-07-15, independent rebuilds from scratch):

| Configuration | Wall power |
|---|---|
| Plain D0, no RTD3 attempted | 28.8-33.5W (varies with driver/config, see below) |
| Audio unbound, GPU pinned D0 (`power/control=on`, no suspend attempted) | 33.35W — same as baseline |
| D3hot (software runtime-suspend only) | 53-54W |
| D3cold (real, hardware-confirmed, audio unbound) | 52-56W |
| GPU driver fully unbound (not just suspended) | 54.8W |

The extra ~20W shows up only once the GPU actually attempts a suspend/D3 transition —
confirmed by the "audio unbound, GPU pinned D0" row: releasing the GPU↔audio device link
alone costs nothing. The full driver-unbind row confirms it isn't about *how* the
transition is reached either (runtime-PM vs. full unbind) — same cost either way. The
mechanism: once nvidia's driver (or the generic PCI/ACPI unbind path) commits to a D3
transition, it behaves as though the board is about to physically cut power to the slot.
Because it doesn't (see below), the GPU is left in a degraded "expecting to die" state
that draws more than its own already-good native D0/P8 idle (2.4-2.9W GPU-only, per
`nvidia-smi`). Matches the upstream bug pattern in
[NVIDIA/open-gpu-kernel-modules#905](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/905).

#### Why the board can't actually cut power

Decompiled the live DSDT directly (`acpidump -b` + `iasl -d`, no SSDT involved): `\_SB.PC00.PEG1`
(the GPU slot) has zero native `_PR3`. Four other devices (`VOL0`-`VOL3`, almost certainly
the USB4/Thunderbolt controllers) *do* have real `_PR3` methods with genuine `PowerResource`
blocks and hardware helpers (`VLON`/`VLOF`). So the firmware architecture supports real
ACPI power-sequencing — ASUS just never wired it to the PCIe x16 slot. Standard desktop
PCIe slots generally don't have an independently switchable power rail at all (unlike a
laptop's soldered Optimus package), so this is almost certainly a hardware limitation, not
a firmware oversight. The `ACPI D3Cold Support` BIOS master switch (`Setup` offset `0x722`)
is not the gap — confirmed enabled and doing nothing without the missing rail hardware.

Our SSDT's `_PR3` `_ON`/`_OFF` methods are empty stubs — there's no register/GPIO behind
them. The kernel's ACPI power-resource protocol is satisfied (an object exists and is
callable), so `pci_set_power_state()` reports success and `power_state` genuinely reads
`D3cold` — but no physical power is ever removed.

#### Driver bugs found and patched (nvidia-open, 610.43.02)

All three in `src/nvidia/arch/nvalloc/unix/src/dynamic-power.c` unless noted. Line numbers
below are current as of the 2026-07-15 rebuild; may drift a line or two between driver
versions.

1. **Notebook-detection gate blocks RTD3 auto-enable on any desktop.**
   `rm_init_dynamic_power_management` (~line 954, and the matching disable-side check
   ~line 1012 in `rm_cleanup_dynamic_power_management`): the gate for calling
   `nv_allow_runtime_suspend()` requires `mode == FINE` *and*
   `dynamic_power_regkey == NV_REG_DYNAMIC_POWER_MANAGEMENT_DEFAULT`. CachyOS's
   `/usr/lib/modprobe.d/nvidia.conf` sets `NVreg_DynamicPowerManagement=0x02` (FINE)
   explicitly — needed to get `mode=FINE` at all, since the undocumented auto-detect path
   (`rm_is_system_notebook()`) resolves to `NEVER` on any desktop with no battery object,
   by design, on GA102+. But setting an explicit regkey value skips auto-detect entirely,
   so `mode==FINE` and `regkey==DEFAULT` can never both be true on a desktop. Fix: drop
   the `regkey==DEFAULT` clause from both gates, leave just `mode==FINE`.

2. **`nv_indicate_idle()` was self-defeating.** `kernel-open/nvidia/nv.c` (~line 5505):
   stock code does `pm_runtime_put_noidle(dev)` then a synthetic read of the GPU's own PCI
   config-space sysfs file to nudge the kernel into checking idleness. But the kernel's
   config-space read handler itself transparently wakes the device first
   (`pci_config_pm_runtime_get`/`put`) to return live register values. Confirmed via
   ftrace kprobes: `nv_indicate_idle` → `pci_config_pm_runtime_get` → `put` → `rpm_idle` →
   `-EBUSY`, all within microseconds — nvidia asks to suspend in the same breath as
   invisibly waking the device. Fix: replace the noidle+read pair with a single
   `pm_runtime_put_sync(dev)`.

3. **`console_device` gate permanently pins the GPU awake.**
   `rm_enable_dynamic_power_management` (~line 1082): the GPU's initial refcount is only
   released `if (mode != NEVER) && !nv->console_device`, where
   `nv->console_device = bUefiConsole || nv->primary_vga`. With no iGPU active, the RTX
   4070 *is* `primary_vga`, so this is permanently true, independent of VRAM, compositor
   state, or target. This is the real blocker — RM's own refcount never reached zero, so
   nothing downstream mattered. Safe to remove on rabble specifically because
   `nvidia_drm fbdev=0` is already set (below), so this GPU never owns a console
   framebuffer anyway — the risk the gate protects against doesn't apply here. Fix: drop
   `!nv->console_device` from both the enable and disable sides.

With all three applied, `dev->power.runtime_status` reaches genuine `suspended`
(`pm_runtime_put_sync` returns `0`, `usage_count=0`) within ~1s of boot, reproduced cleanly
both times this has been built.

#### The audio device link, and what it actually costs

`0000:01:00.1` (GPU's HDMI/DP audio function) is a `device_link` consumer of the GPU. While
it's active, the link keeps the GPU pinned regardless of the GPU's own state.
`snd_hda_intel`'s `power_save` autosuspend never fires on this codec no matter how it's
configured (tested with a real PCM open/close cycle to rule out "timer never armed") — the
only thing that reliably suspends it is a full driver unbind.

2026-07-15 isolated this cleanly: with audio unbound and the GPU explicitly pinned to D0
(`power/control=on`, no suspend allowed), wall power reads 33.35W — identical to normal
baseline. So the unbound audio device costs nothing by itself. It's only ever the
precondition that lets the GPU attempt a D3 transition; the ~20W cost is the GPU's own
transition attempt, not the audio device sitting unbound. (This corrects the original
2026-07-12 writeup, which suspected the audio device itself as the likely cost and left it
unproven.)

A full PCI-level unbind of the GPU driver itself (not just runtime-suspending it) costs the
same ~55W — confirms the cost isn't specific to the runtime-PM path either.

#### A real driver bug found as a side effect

Waking the GPU from genuine D3cold via a raw config-space read (`lspci -vvv`, `nvidia-smi`
while suspended) races an automatic re-suspend attempt and can hit
`NVRM: Recursive acquire of the GPU alloc lock or locking order violation @ locks.c:934`,
`nv_pmops_runtime_suspend returned -5`. `pm_runtime` then latches `runtime_status` into
`error` permanently — `power/control` toggling doesn't clear it, only a reboot does. Likely
the exact mechanism behind the community-reported #905 cycling bug. Use passive
`cat .../power/runtime_status` for checks around a device that might be suspended; never
`lspci -vvv` or `nvidia-smi`.

#### Reproducing this from a clean install

Everything below is fully reversible and was torn back down after each test. Nothing here
persists on rabble day to day except `nvidia_drm fbdev=0` (a real, independent bug fix —
see below).

**1. BIOS RC vars** (direct EFI variable write, no physical BIOS entry needed — see
`capture_bios.py`/`restore_bios.py`):

```python
setup = '/sys/firmware/efi/efivars/Setup-ec87d643-eba4-4bb5-a1e5-3f3e36b20da9'
sa    = '/sys/firmware/efi/efivars/SaSetup-72c5e28c-7783-43a1-8767-fad73fccafa4'
# chattr -i both files first, chattr +i after
# Setup[0x5E]  = 1   Low Power S0 Idle Capability
# Setup[0x722] = 1   ACPI D3Cold Support (RTD3 master switch)
# SaSetup[0x37F/0x380/0x381] = 3   PEG1/2/3 L1 Substates (L1.1+L1.2)
```

**2. SSDT override** — source is `nvidia-d3.dsl` in this repo:

```bash
iasl nvidia-d3.dsl                          # -> nvidia-d3.aml
sudo mkdir -p /etc/acpi/override
sudo cp nvidia-d3.aml /etc/acpi/override/
```

`/etc/initcpio/install/acpi_override`:

```bash
#!/bin/bash
build() {
    local dir="${EARLYROOT:-$BUILDROOT}/kernel/firmware/acpi"
    mkdir -p "$dir"
    for f in /etc/acpi/override/*.aml; do
        [ -e "$f" ] || continue
        cp "$f" "$dir/"
    done
}
```

Add `acpi_override` to `HOOKS=(...)` in `/etc/mkinitcpio.conf` (anywhere before
`filesystems` is fine — it just needs to run during build). The hook must write to
`$EARLYROOT`, not `$BUILDROOT`: the kernel only scans the early uncompressed CPIO for
`kernel/firmware/acpi/`.

**3. Driver source patches** — swap to buildable source, apply the three patches above,
rebuild:

```bash
sudo pacman -R linux-cachyos-nvidia-open linux-cachyos-lts-nvidia-open
sudo pacman -S nvidia-open-dkms
# edit /usr/src/nvidia-<ver>/src/nvidia/.../dynamic-power.c and kernel-open/nvidia/nv.c
sudo dkms build nvidia/<ver> -k $(uname -r) --force
sudo dkms install nvidia/<ver> -k $(uname -r) --force
# repeat build/install for the -lts kernel too if you run both
```

**4. modprobe flags** (`/etc/modprobe.d/nvidia-power.conf`, test-only):

```
options nvidia NVreg_EnableS0ixPowerManagement=1
```

**5. Rebuild initramfs, reboot:** `sudo mkinitcpio -P`

**6. Verify:**

```bash
sudo dmesg | grep RTND3                      # SSDT loaded from initramfs
cat /proc/driver/nvidia/gpus/*/power         # Runtime D3 status: Enabled (fine-grained)
```

**7. Unbind console and audio** (both live, no reboot, both reversible via `bind`):

```bash
echo simple-framebuffer.0 | sudo tee /sys/bus/platform/drivers/simple-framebuffer/unbind
echo 0000:01:00.1 | sudo tee /sys/bus/pci/drivers/snd_hda_intel/unbind
```

Then watch `cat /sys/bus/pci/devices/0000:01:00.0/power/runtime_status` — should reach and
hold `suspended`.

**Reverting:** rebind console and audio (`bind` instead of `unbind`, same paths), set
`power/control` back to `auto` on the GPU, zero out the three BIOS vars, delete
`/etc/acpi/override`, `/etc/initcpio/install/acpi_override`, remove `acpi_override` from
`HOOKS`, delete `nvidia-power.conf`, swap back to `linux-cachyos-nvidia-open` +
`linux-cachyos-lts-nvidia-open`, `mkinitcpio -P`, reboot. Check `pacman -Qtdq` afterward —
the DKMS build pulls in `cmake`/`dkms`/`vulkan-headers` as dependencies that become orphans
once you swap back; `pacman -Rns` them.

`nvidia_drm fbdev=0` (`/etc/modprobe.d/nvidia-drm-fbdev.conf`) is the one thing to keep
regardless — see below.

#### Console binding: independent of all of the above

`simpledrm` (the generic boot-console framebuffer) binds to whichever GPU actually has a
live display attached at POST — not whichever the BIOS `Primary Display` setting prefers.
Enabling the iGPU and setting `Primary Display: CPU Graphics` in BIOS does *not* move the
console off the discrete GPU if nothing is physically connected to the iGPU's output; GOP
follows the live display, not the BIOS preference. `video=efifb:off` and blacklisting
`simpledrm` both no-op on this kernel — `simpledrm` is compiled in, not a module, and this
kernel's sysfb path doesn't respond to the legacy `efifb` flag.

Forcing a connector with `video=<connector>:<mode>e` (e.g. `video=HDMI-A-2:1920x1080@60e`)
does work — it gets `i915` its own real fbdev even with nothing plugged in. But it doesn't
evict `simpledrm` from the nvidia GPU, because that eviction is a side effect of a KMS
driver registering its *own* competing fbdev, which is exactly what `nvidia_drm fbdev=0`
disables. There's no way to get both "nvidia never owns a console framebuffer" and "something
else evicts the boot console from the nvidia GPU" without either re-enabling
`nvidia_drm.fbdev` (reintroducing the original problem) or blacklisting `simpledrm` at the
kernel-build level (not available via a running kernel's boot config on this system).

`simple-framebuffer` can be unbound and rebound live via sysfs regardless of any of this —
see step 7 above. Confirmed via direct A/B (`nvidia-smi --query-gpu=pstate,power.draw`):
bound or unbound, the GPU sits at the same P8/~2.5W idle. The live console binding was
never the actual blocker for anything — `nv->console_device`/`primary_vga` (a static
boot-time PCI designation, patched in step 3 above) is a completely different mechanism
from whether `simpledrm` happens to be bound at the moment you check.

#### The missing ~6W: GSP firmware, not driver/kernel version (2026-07-10)

The old Proxmox-era host (same board) idled at ~23-24W; this install sits at ~33.5W. Root
cause: the old host ran the proprietary driver with `NVreg_EnableGpuFirmware=0` (GSP
disabled). That flag only works on the proprietary driver — the open kernel modules
require GSP on Ada-generation cards, no way around it.

Verified directly: installed the proprietary driver (`nvidia-580xx-dkms`, supports Ada)
temporarily. With GSP off (confirmed via `nvidia-smi -q | grep -i gsp` → `N/A`) and
everything else matched (no DRM/modeset loaded idle, audio `power_save=1`, persistence
mode), wall power held at ~28W. Reverting only the GSP setting brought it back to ~34W — a
clean, isolated 6W delta. This is the entire gap; not kernel version, not distro, not
driver version. Separate and additive to whatever D3cold would be worth — not pursued
further since it was only validated at idle, not under gaming load, and the proprietary
driver swap wasn't kept for that reason.

Also tried and ruled out along the way: fully unbinding the GPU driver to force D3cold
(reproduces the #905 bounce-back bug, 48.5W, worse than leaving it alone); removing the
`_PR3` SSDT to see if D3hot would stabilize without it (it doesn't — just stops the kernel
from attempting any runtime suspend at all, same 28.8W as with the SSDT present).
