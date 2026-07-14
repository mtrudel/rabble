### BIOS EFI variable tweaks

The BIOS exposes many power-relevant settings that are not visible in the standard
ASUS GUI. These can be written directly to EFI variable files from Linux; the Intel
Reference Code reads them at POST time on the next boot.

No RC-only (hidden, non-GUI) EFI vars are currently set away from their IFR factory
defaults. There were three, all exclusively in service of the RTD3 investigation
(see gpu.md — RTD3 was conclusively a net power loss and fully backed out):

| Variable | Offset | Default | Was set to | Description |
|----------|--------|---------|------------|-------------|
| Setup | 0x5E | 0 | 1 | Low Power S0 Idle Capability — hidden master switch; tells Intel RC to set the ACPI S0ID flag natively (replaces the backed-out `nvidia-s0ix.dsl` SSDT approach) |
| Setup | 0x722 | 0 | 1 | ACPI D3Cold Support — hidden master switch; tells Intel RC to generate `_PR3` power resources in ACPI tables, enabling RTD3 for discrete GPU |
| SaSetup | 0x37F–0x381 | 0 | 3 | PEG1–PEG3 L1 Substates → L1.1+L1.2 — required for PCIe link to enter the deep idle state that RTD3 depends on |

All three reverted to factory default (0) once RTD3 was ruled out. `bios_snapshot.json`'s
`rc_settings` is now empty to match.

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
