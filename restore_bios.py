#!/usr/bin/env python3
"""
Diff or restore BIOS settings from bios_snapshot.json.

Usage:
  python3 restore_bios.py              # show diff vs current EFI vars (dry run)
  sudo python3 restore_bios.py --apply # write all differing settings, then reboot
"""
import sys, os, json, subprocess

EFIVARS   = "/sys/firmware/efi/efivars"
SNAP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bios_snapshot.json")
apply     = "--apply" in sys.argv

snap = json.load(open(SNAP_FILE))
all_settings = (
    [(s["file"], int(s["offset"], 16), s["size"], s["value"], s["description"], "GUI")
     for s in snap["settings"]]
  + [(s["file"], int(s["offset"], 16), s["size"], s["value"], s["description"], "RC")
     for s in snap["rc_settings"]]
)

# Read each EFI variable file once
file_data = {}
for fname, *_ in all_settings:
    if fname not in file_data:
        path = os.path.join(EFIVARS, fname)
        try:
            file_data[fname] = bytearray(open(path, "rb").read())
        except Exception as e:
            print(f"SKIP {fname}: {e}", file=sys.stderr)
            file_data[fname] = None

pending  = {}
n_change = 0

print(f"  {'OFFSET':>7}  {'CUR':>5}  {'SNAP':>5}  DESCRIPTION")
print("  " + "─" * 78)

cur_section = None
for fname, offset, size, snap_val, desc, section in all_settings:
    if section != cur_section:
        cur_section = section
        label = "RC SETTINGS (hidden)" if section == "RC" else "GUI SETTINGS"
        print(f"\n  # {label}")

    raw = file_data.get(fname)
    if raw is None:
        continue
    file_off  = offset + 4
    byte_size = size // 8
    if file_off + byte_size > len(raw):
        print(f"  {'?':>7}  {'?':>5}  {snap_val:5d}  {desc[:60]}  [offset OOB]")
        continue

    if size == 8:
        cur = raw[file_off]
    elif size == 16:
        cur = int.from_bytes(raw[file_off:file_off+2], "little")
    else:
        cur = int.from_bytes(raw[file_off:file_off+4], "little")

    differs = cur != snap_val
    if differs:
        n_change += 1
        marker = "*"
        if apply:
            if fname not in pending:
                pending[fname] = bytearray(raw)
            if size == 8:
                pending[fname][file_off] = snap_val & 0xFF
            elif size == 16:
                pending[fname][file_off:file_off+2] = snap_val.to_bytes(2, "little")
            else:
                pending[fname][file_off:file_off+4] = snap_val.to_bytes(4, "little")
    else:
        marker = " "

    print(f"{marker} 0x{offset:04X}  {cur:5d}  {snap_val:5d}  {desc[:60]}")

print()
if not n_change:
    print("All settings match snapshot.")
    sys.exit(0)

if not apply:
    print(f"Dry run — {n_change} difference(s). Re-run with --apply as root.")
    sys.exit(0)

if os.geteuid() != 0:
    print("ERROR: --apply requires root", file=sys.stderr)
    sys.exit(1)

for fname, new_data in pending.items():
    path = os.path.join(EFIVARS, fname)
    print(f"Writing {fname}...")
    subprocess.run(["chattr", "-i", path], check=True)
    try:
        fd = os.open(path, os.O_WRONLY)
        try:
            os.write(fd, bytes(new_data))
        finally:
            os.close(fd)
        print("  OK")
    finally:
        subprocess.run(["chattr", "+i", path], check=True)

print("\nDone. Reboot for changes to take effect.")
