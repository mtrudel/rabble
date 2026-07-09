#!/usr/bin/env python3
"""
Snapshot all BIOS settings that differ from IFR defaults.

Parses the AMI IFR (extracted from the live BIOS flash) to find every
GUI-visible setting that has been changed from its factory default, then
writes bios_snapshot.json. The IFR is cached in ~/ami_setup.bin (survives
reboots) and auto-regenerated when missing or when --regen-ifr is passed.

Usage (run on rabble as root):
  sudo python3 capture_bios.py             # use cached IFR
  sudo python3 capture_bios.py --regen-ifr # re-extract IFR from flash first
"""
import os, sys, json, re, subprocess, shutil
from datetime import date

SETUP_BIN  = os.path.expanduser("~/ami_setup.bin")
IFR_FILE   = SETUP_BIN + ".0.0.en-US.uefi.ifr.txt"
BIOS_IMAGE = "/tmp/bios_flash.bin"
BIOS_DUMP  = BIOS_IMAGE + ".dump"
SETUP_GUID = "899407D7-99FE-43D8-9A21-79EC328CAC21"
EFIVARS    = "/sys/firmware/efi/efivars"
OUT        = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bios_snapshot.json")

VARMAP = {
    "Setup":    "Setup-ec87d643-eba4-4bb5-a1e5-3f3e36b20da9",
    "CpuSetup": "CpuSetup-b08f97ff-e6e8-4193-a997-5e9e9b0adb32",
    "PchSetup": "PchSetup-4570b7f1-ade8-4943-8dc3-406472842384",
    "SaSetup":  "SaSetup-72c5e28c-7783-43a1-8767-fad73fccafa4",
}

RC_SETTINGS = [
    ("Setup",   0x005E, 8, "Low Power S0 Idle Capability (S0ix master switch)"),
    ("Setup",   0x0722, 8, "ACPI D3Cold Support (GPU RTD3 master switch)"),
    ("SaSetup", 0x037F, 8, "PEG1 L1 Substates → L1.1+L1.2 (GPU slot)"),
    ("SaSetup", 0x0380, 8, "PEG2 L1 Substates → L1.1+L1.2"),
    ("SaSetup", 0x0381, 8, "PEG3 L1 Substates → L1.1+L1.2"),
]
RC_KEYS = {(var, offset) for var, offset, *_ in RC_SETTINGS}


# ── IFR extraction ────────────────────────────────────────────────────────────

def regen_ifr():
    print("Reading BIOS flash (this takes ~30s)...", file=sys.stderr)
    subprocess.run(
        ["flashrom", "-p", "internal", "--ifd", "-i", "bios", "-r", BIOS_IMAGE],
        check=True, capture_output=True,
    )
    print("Extracting UEFI modules...", file=sys.stderr)
    shutil.rmtree(BIOS_DUMP, ignore_errors=True)
    subprocess.run(["uefiextract", BIOS_IMAGE, "all"], check=True, capture_output=True)

    setup_body = None
    for root, _, files in os.walk(BIOS_DUMP):
        if SETUP_GUID.lower() in root.lower() and "body.bin" in files:
            setup_body = os.path.join(root, "body.bin")
            break
    if not setup_body:
        sys.exit(f"ERROR: Setup module {SETUP_GUID} not found in BIOS dump")

    shutil.copy(setup_body, SETUP_BIN)
    print("Decoding IFR...", file=sys.stderr)
    subprocess.run(["ifrextractor", SETUP_BIN], check=True, capture_output=True)
    if not os.path.exists(IFR_FILE):
        sys.exit(f"ERROR: ifrextractor did not produce {IFR_FILE}")
    print(f"IFR ready: {IFR_FILE}", file=sys.stderr)


# ── IFR parser ────────────────────────────────────────────────────────────────

vs_pat       = re.compile(
    r'VarStore Guid: [0-9A-Fa-f\-]+, VarStoreId: (0x[0-9A-Fa-f]+), '
    r'Size: (?:0x[0-9A-Fa-f]+|\d+), Name: "([^"]+)"'
)
q_pat        = re.compile(
    r'(?:OneOf|CheckBox|Numeric) Prompt: "([^"]*)".*?'
    r'VarStoreId: (0x[0-9A-Fa-f]+), VarOffset: (0x[0-9A-Fa-f]+).*?Size: (\d+)'
)
q_start      = re.compile(r'^\s*(?:OneOf|CheckBox|Numeric) ')
q_end        = re.compile(r'^\s*(?:EndOneOf|EndCheckBox|EndNumeric)\b')
form_pat     = re.compile(r'Form FormId: [^,]+, Title: "([^"]+)"')
def_pat      = re.compile(r'Default DefaultId: 0x0 Value: (0x[0-9A-Fa-f]+|-?\d+)')
opt_pat      = re.compile(r'OneOfOption Option: "[^"]*" Value: (0x[0-9A-Fa-f]+|\d+)(.*)')


def parse_val(s):
    return int(s, 16) if s.startswith("0x") else int(s)


def parse_ifr(ifr_path):
    """Return list of (var_name, offset, size, default, prompt) for all questions."""
    vsid_to_var = {}
    questions   = []
    seen        = set()

    cur_form  = None
    q_pend    = None   # (prompt, vsid, offset, size)
    q_def     = None   # default found outside SuppressIf
    q_def_sup = None   # default found inside SuppressIf (fallback)
    cond_depth = 0     # nesting depth of any conditional block
    sup_depth  = 0     # nesting depth of SuppressIf specifically
    line_buf  = None   # for multi-line question declarations

    def finalize():
        nonlocal q_pend, q_def, q_def_sup
        if q_pend is None:
            return
        prompt, vsid, offset, size = q_pend
        effective = q_def if q_def is not None else q_def_sup
        var = vsid_to_var.get(vsid)
        key = (var, offset)
        if var and effective is not None and size in (8, 16, 32) and key not in seen:
            seen.add(key)
            questions.append((var, offset, size, effective, prompt, cur_form or ""))
        q_pend = q_def = q_def_sup = None

    with open(ifr_path) as f:
        for raw in f:
            s = raw.strip()

            # Multi-line question accumulation
            if line_buf is not None:
                line_buf += " " + s
                if "VarStoreId:" in line_buf and "Size:" in line_buf:
                    s = raw = line_buf
                    line_buf = None
                else:
                    continue

            m = vs_pat.search(raw)
            if m:
                vsid, name = int(m.group(1), 16), m.group(2)
                if name in VARMAP:
                    vsid_to_var[vsid] = name
                continue

            m = form_pat.search(raw)
            if m:
                finalize()
                cur_form  = m.group(1)
                cond_depth = sup_depth = 0
                continue

            if s.startswith("SuppressIf"):
                cond_depth += 1; sup_depth += 1; continue
            if s.startswith(("GrayOutIf", "DisableIf")):
                cond_depth += 1; continue
            if s.startswith("EndIf") and cond_depth:
                if sup_depth and sup_depth == cond_depth:
                    sup_depth -= 1
                cond_depth -= 1
                continue

            if q_end.match(s):
                finalize()
                continue

            # Question start — may be multi-line
            if q_start.match(s):
                if "VarStoreId:" not in raw:
                    line_buf = s
                    continue
                finalize()
                m = q_pat.search(raw)
                if m:
                    prompt, vsid_h, off_h, size_s = m.groups()
                    q_pend = (prompt.strip(), int(vsid_h, 16),
                              int(off_h, 16), int(size_s))
                    q_def = q_def_sup = None
                continue

            if q_pend is None:
                continue

            m = def_pat.search(raw)
            if m:
                v = parse_val(m.group(1))
                if sup_depth:
                    if q_def_sup is None: q_def_sup = v
                else:
                    if q_def is None: q_def = v
                continue

            m = opt_pat.search(raw)
            if m and re.search(r'\bDefault\b', m.group(2)):
                v = parse_val(m.group(1))
                if sup_depth:
                    if q_def_sup is None: q_def_sup = v
                else:
                    if q_def is None: q_def = v

    finalize()
    return questions


# ── EFI variable reader ───────────────────────────────────────────────────────

def read_efi():
    data = {}
    for name, fname in VARMAP.items():
        path = os.path.join(EFIVARS, fname)
        try:
            data[name] = open(path, "rb").read()[4:]
        except Exception as e:
            print(f"WARNING: cannot read {fname}: {e}", file=sys.stderr)
    return data


def read_val(efi, var, offset, size):
    d = efi.get(var)
    if d is None or offset + size // 8 > len(d):
        return None
    if size == 8:  return d[offset]
    if size == 16: return int.from_bytes(d[offset:offset+2], "little")
    if size == 32: return int.from_bytes(d[offset:offset+4], "little")


def to_entry(var, offset, size, val, desc):
    return {"file": VARMAP[var], "offset": f"0x{offset:04X}",
            "size": size, "value": val, "description": desc}


# ── Main ──────────────────────────────────────────────────────────────────────

if "--regen-ifr" in sys.argv or not os.path.exists(IFR_FILE):
    if not os.path.exists(IFR_FILE):
        print("IFR cache missing — extracting from flash...", file=sys.stderr)
    regen_ifr()

print("Parsing IFR...", file=sys.stderr)
questions = parse_ifr(IFR_FILE)
print(f"  {len(questions)} questions with parseable defaults", file=sys.stderr)

efi = read_efi()

gui_settings = []
for var, offset, size, default, prompt, form in questions:
    if (var, offset) in RC_KEYS:
        continue
    cur = read_val(efi, var, offset, size)
    if cur is None or cur == default:
        continue
    gui_settings.append(to_entry(var, offset, size, cur, prompt))

rc_settings = []
for var, offset, size, desc in RC_SETTINGS:
    cur = read_val(efi, var, offset, size)
    if cur is None:
        print(f"WARNING: cannot read {var}[0x{offset:04X}]", file=sys.stderr)
        continue
    rc_settings.append(to_entry(var, offset, size, cur, desc))

snapshot = {
    "machine":     "rabble (ASUS ROG STRIX B760-I GAMING WIFI)",
    "captured":    str(date.today()),
    "settings":    gui_settings,
    "rc_settings": rc_settings,
}

with open(OUT, "w") as f:
    json.dump(snapshot, f, indent=2)
    f.write("\n")

print(f"GUI settings changed from default: {len(gui_settings)}", file=sys.stderr)
print(f"RC settings: {len(rc_settings)}", file=sys.stderr)
print(f"Written: {OUT}", file=sys.stderr)
