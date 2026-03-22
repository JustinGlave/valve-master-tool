# Valve Master Tool

**Phoenix valve model number decoder, validator, and guided builder.**

---

## What It Does

Valve Master Tool (VMT) takes a Phoenix valve model number and instantly breaks it down into every field — product line, construction, size, pressure, actuator type, controller, orientation, fail-safe, options, and more — then validates the configuration against Phoenix product rules and displays the operating flow table for that valve.

It also works in reverse: if you don't have a model number yet, you can use the guided builder to click through valid field choices and construct one from scratch.

---

## Who It's For

- **Service technicians** who need to quickly identify what parts are on a valve or what spare parts to order
- **Engineers** who need to validate that a model number is correctly configured before submitting an order
- **Sales and applications teams** who need to look up flow data or confirm option compatibility for a given product

---

## Key Features

### Decode & Validate
Paste any Phoenix model number and immediately see:
- Every field decoded in plain English (e.g. `Actuator Type: Linear high-speed electric, IP56`)
- Validation issues highlighted in red — invalid codes, incompatible combinations, and rule violations
- The operating flow table for that valve (CFM ranges by size, single and dual body)
- Product notes relevant to the specific configuration

### Guided Builder
Click any field card to open a picker showing all available options for that field. Valid options are shown in white, invalid ones in grey with the reason why. Double-click to apply — the model number updates live.

### Spare Parts Lookup
Field pickers and option dialogs show relevant spare part numbers inline, so you can identify what to order without leaving the tool. Parts are context-aware — a PSL pressure switch assembly, for example, returns the correct part number based on the valve's pressure rating and body count.

### Quick Test Models
The interface includes a set of pre-loaded valid and intentionally failing model numbers so you can verify the tool is working correctly at a glance.

### Auto-Updater
VMT checks GitHub for new releases on startup. When an update is available, a green banner appears in the status bar. Click **Install & Restart** to download and apply the update automatically — no manual file replacement needed.

---

## Supported Product Lines

| Product Line      | Prefixes  |
|-------------------|-----------|
| Celeris II        | MAV, EXV  |
| Theris            | HSV, HEV  |
| Traccel           | TSV, TEV  |
| CSCP              | PVE, PVS  |
| Base Upgradeable  | BSV, BEV  |
| Analog            | MAV, EXV (via Analog Mode checkbox) |

---

## Model Number Format

Phoenix model numbers follow this structure:

```
[PREFIX][CONSTRUCTION][BODIES][SIZE][PRESSURE]-[DESIGN][ACTUATOR][CONTROLLER][ORIENTATION][FAILSAFE]-[PROTOCOL]-[OPTIONS]
```

**Example:** `PVEA110M-AMBHY-BMT-PSL`

| Segment | Value | Meaning |
|---------|-------|---------|
| `PVE`   | Type         | Phoenix Valve: Exhaust |
| `A`     | Chemical Resistance | Class A — uncoated aluminum |
| `1`     | Bodies       | Single body |
| `10`    | Size         | 10-inch |
| `M`     | Pressure     | Medium (0.6"–3.0" WC) |
| `A`     | Body Design  | Standard |
| `M`     | Actuator Type | Linear high-speed electric, IP56 |
| `B`     | Controller   | ACM without BLE |
| `H`     | Orientation  | Horizontal |
| `Y`     | Fail-Safe    | Programmable fail-safe position |
| `BMT`   | Protocol     | BACnet MS/TP |
| `PSL`   | Option       | Pressure switch, low limit |

---

## Files

| File | Purpose |
|------|---------|
| `valve_master_backend.py` | All parsing, decoding, validation, flow tables, and spare parts logic |
| `valve_master_pyside6.py` | Desktop GUI (PySide6) |
| `version.py` | App version string |
| `updater.py` | GitHub Releases auto-updater |

Both `valve_master_backend.py` and `valve_master_pyside6.py` must be in the same directory to run.

---

## Running from Source

**Requirements:** Python 3.10 or later, PySide6

```
pip install PySide6
python valve_master_pyside6.py
```

---

## Building the Executable

A packaged Windows `.exe` is built with PyInstaller via the included build script:

```
build.bat
```

Output:
- `dist\ValveMasterTool\` — full distributable folder
- `dist\ValveMasterTool.zip` — exe-only zip for GitHub Release uploads

See `GIT_SETUP.md` for the full release workflow.

---

## Installation Notes

- Install the app in a **local folder** (e.g. `C:\Tools\ValveMasterTool\`)
- Do **not** run from OneDrive, Dropbox, or other cloud-synced folders — file locking will cause auto-updates to fail
- VMT will warn you on startup if it detects a synced folder

---

*Valve Master Tool is an internal Phoenix Controls engineering utility.*
