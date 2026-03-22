# valve_master_backend.py
# Valve Master Tool backend

from dataclasses import dataclass, field

APP_NAME = "Valve Master Tool"

PRODUCT_DISPLAY_NAMES = {
    "CELERIS_II": "Celeris II",
    "THERIS": "Theris",
    "TRACCEL": "Traccel",
    "CSCP": "CSCP",
    "BASE_UPGRADEABLE": "Base Upgradeable",
    "ANALOG": "Analog",
    "UNKNOWN": "Unknown",
}

@dataclass
class ParsedModel:
    full_model: str
    product_line: str
    base: str
    suffix: str
    prefix: str
    construction: str
    qty_char: str
    size_code: str
    pressure: str
    design_char: str
    control_type: str
    controller: str
    orientation: str
    failsafe: str
    protocol: str = ""
    options: list[str] = field(default_factory=list)

@dataclass
class OperatingTable:
    title: str
    pressure_drop: str
    rows: list[dict[str, str]]

notes_celerisii = {
    "D": "Note 1: Construction D is ONLY available in single-body valves (Number of Bodies = F or 1) WITHOUT square flanges (Options SFB or SFX). Rectangular plates can be purchased as special products to field assemble two, three or four single-body round-flanged valves into multi-body configurations. For sizes 08, 10, and 12 only.",
    "H_controller": "Note 2: Celeris Hood valves cannot have Low Speed actuators (Control Type = H, I, and L).",
    "REO": "Note 4: Option REO: Remote Electronics, Outdoor installations ONLY. Limited to PNEUMATICALLY actuated valves ONLY (Control Type = N). HORIZONTAL orientation ONLY.",
    "SFB_SFX": "Note 1: See construction rules for square flanges (applies when SFB or SFX is used).",
}

notes_theris = {
    "08": "Note 1: 8-inch shut-off Valves (Design = S or L) are available ONLY in Construction = A (uncoated).",
    "14": "Note 2: 14-inch valves are currently NOT available as Low Leakage Shut-off (Design = L) with Medium Pressure (Range = M).",
    "S_low_pressure": "Note 3: Low Pressure (Range = L), Standard Shut-off (Design = S) valves are NOT available in Orientation U (vertical upflow).",
    "L_low_pressure": "Note 4: Low Pressure (Range = L), Low Leakage (Design = L) valves are currently NOT available in any size.",
    "WRE_lonmark": "Note 7: Option WRE with Theris LonMark valves is limited to Valve Controllers E, O, or X ONLY.",
}

shared_notes = {
    "REI": "Note 5: Option REI: Remote Electronics, indoor installations ONLY.",
    "WRE": "Note 6: Option WRE: Weather Resistant Electronics, outdoor installations.",
}

analog_notes = [
    '1. Pressure switch set point = 0.3" WC (75 Pa).',
    '2. All hood exhaust booster valves must have "P" type controllers and pressure switches.',
]

notes_cscp = {
    "06": "CSCP Note: Size 06 is limited to Bodies = F or 1, Pressure Rating = M only, Body Design = A only, and Orientation = H or U only.",
    "08": "CSCP Note: Size 08 is limited to Bodies = F or 1 only.",
    "E": "CSCP Note: Chemical Resistance E is limited to Size 10 or 12 only and Body Design = A only.",
    "F": "CSCP Note: Chemical Resistance F is limited to Size 10 or 12 only and Body Design = A only.",
    "C_controller": "CSCP Note: Actuator Type C requires Controller Type = N only.",
    "F_controller": "CSCP Note: Actuator Type F requires Controller Type = N only, Bodies = 2, and Size = 10 or 12 only.",
    "H_controller": "CSCP Note: Actuator Type H is limited to Size 06, 08, 10, or 12 with Controller Type = P or T only.",
    "I_controller": "CSCP Note: Actuator Type I is limited to Size 08, 10, 12, or 14 with Controller Type = N, P, or T only.",
    "L_controller": "CSCP Note: Actuator Type L requires Controller Type = P or T only.",
    "M_controller": "CSCP Note: Actuator Type M requires Controller Type = B or D only.",
    "T_controller": "CSCP Note: Actuator Type T requires Controller Type = N only.",
    "EVI": "CSCP Note: Option EVI is limited to Type = PVE only.",
    "LCL": "CSCP Note: Option LCL is limited to Design = A and Sizes 08, 10, 12, or 14 only. Size 14 is further limited to 1600 CFM.",
    "REI": "CSCP Note: Option REI is limited to Controller Type = B, D, or P only.",
    "SFB": "CSCP Note: Option SFB is limited to Bodies = 1 and Chemical Resistance = A, B, or C only.",
    "SFD": "CSCP Note: Option SFD is limited to Bodies = 1 and Chemical Resistance = A, B, or C only.",
    "SFI": "CSCP Note: Option SFI is limited to Bodies = 1 and Chemical Resistance = A, B, or C only.",
    "SSB": "CSCP Note: Option SSB is limited to Chemical Resistance = A and Body Design = A only.",
}

notes_base_upgradeable = {
    "1": "Note 1: Valve Construction D is ONLY available in single-body valves (Bodies = F or 1) of Design A without square flanges (Options SFB, SFD, or SFI).",
    "2": "Note 2: For flange bolt-hole patterns refer to MKT-0061 Flanges For Single Body Valves.",
    "3": "Note 3: 8-inch shut-off valves (Design = L and S) are ONLY available in Valve Construction A (uncoated).",
    "4": "Note 4: 14-inch medium pressure (Range = M), low leakage shutoff valves (Valve Design = L) are NOT available.",
    "5": "Note 5: 14-inch valves with Control Types Q and S are ONLY available as singles (Bodies = F or 1).",
    "6": 'Note 6: Pressure switch alarm set point: 0.3" WC for medium pressure and 0.2" WC for low pressure valves.',
    "7": "Note 7: Low pressure (Range = L), low leakage shut-off valves (Valve Design = L) are NOT available in any size.",
    "8": "Note 8: Low pressure (Range = L), standard shut-off valves (Valve Design = S) are NOT available as vertical up (Valve Orientation = U).",
    "9": "Note 9: Control Types Q and S REQUIRE flow feedback (Valve Controller Designation = F).",
    "10": "Note 10: Control Type T is ONLY available with Valve Controller Designation N, since it has built-in flow feedback.",
    "11": "Note 11: Valve Option EVI is ONLY available on exhaust valves (BEV); NOT available with IBO.",
    "12": "Note 12: Valve Option IBO is available on exhaust and supply valves (BEV and BSV); NOT available with EVI.",
    "13": "Note 13: Valve Option REI, for Control Types Q and S only: Remote Electronics, Indoor Installations ONLY.",
    "14": "Note 14: Valve Options SFB, SFD, or SFI cannot be ordered with Valve Construction D, Bodies F, 2, 3 or 4, nor with each other.",
}

orientation_map = {
    "H": "Horizontal",
    "U": "Vertical upflow",
    "D": "Vertical downflow",
}

standard_product_configs = {
    "CELERIS_II": {
        "family_label": "Valve Family",
        "construction_label": "Construction",
        "bodies_label": "Bodies",
        "size_label": "Size",
        "pressure_label": "Pressure",
        "design_label": "Valve Design",
        "control_label": "Control Type",
        "controller_label": "Controller",
        "orientation_label": "Orientation",
        "failsafe_label": "Fail-Safe",
        "family_map": None,
        "construction_map": {
            "A": "Body and cone uncoated aluminum; shaft uncoated 316 stainless steel",
            "B": "Body and cone baked-on phenolic coating; PFA-coated 316 stainless steel shaft",
            "D": "Body and cone with PVDF coating; hardware with PVDF or baked-on epoxy phenolic coating; PFA-coated 316 stainless steel shaft; see Note 1",
        },
        "bodies_map": {
            "F": "One valve body with welded circular flanges",
            "1": "Single valve body (no flange)",
            "2": "Dual valve (2 bodies)",
            "3": "Three valve bodies (triple)",
            "4": "Four valve bodies (quad)",
        },
        "size_map": {"08": "8 inch", "10": "10 inch", "12": "12 inch", "14": "14 inch"},
        "pressure_map": {"L": "Low pressure 0.3 W.C.- 3.0 W.C.", "M": "Medium pressure 0.6 W.C.- 3.0 W.C."},
        "design_map": {
            "S": "Standard shut-off valve (metal-on-metal seal)",
            "L": "Low leakage shut-off valve (gasketed seal)",
            "A": "Conical shape diffuser",
        },
        "control_map": {
            "H": "Rotary, low-speed electric actuator; NEMA 1; on single 8, 10, and 12 only",
            "I": "Rotary, low-speed electric actuator; IP54",
            "L": "Linear, low-speed electric actuator; IP56",
            "M": "Linear, high-speed electric actuator; IP56",
            "N": "Linear, pneumatic actuator",
        },
        "controller_map": {"E": "Electronic controller", "H": "Hood exhaust valve with pressure switch"},
        "orientation_map": orientation_map,
        "failsafe_map": {"C": "Normally closed", "O": "Normally open", "Z": "Fails to last position"},
        "option_map": {
            "B": "Two single square flanges mounted on both ends of single body valves",
            "F": "One single square flange",
            "M": "Module, scaling function",
            "P": "Pressure switch",
            "PSL": "Pressure switch, low limit",
            "O": "Power supply, valve-mounted, 120 V",
            "R": "Remote electronics",
            "T": "Power supply, valve-mounted, 230 V",
            "REI": "Remote electronics - indoor",
            "REO": "Remote electronics - outdoor",
            "WRE": "Weather resistant electronics",
            "SFB": "Square flanges on both ends",
            "SFX": "Square flange option",
        },
    },
    "THERIS": {
        "family_label": "Valve Family",
        "construction_label": "Construction",
        "bodies_label": "Bodies",
        "size_label": "Size",
        "pressure_label": "Pressure",
        "design_label": "Valve Design",
        "control_label": "Control Type",
        "controller_label": "Controller",
        "orientation_label": "Orientation",
        "failsafe_label": "Fail-Safe",
        "family_map": None,
        "construction_map": {
            "A": "Body and cone uncoated aluminum; shaft uncoated 316 stainless steel",
            "B": "Body and Cone Baked-on Phenolic Coating: PFA Coated 316 Stainless Steel Shaft.",
        },
        "bodies_map": {
            "F": "One valve body with welded circular flanges",
            "1": "Single valve body (no flange)",
            "2": "Dual valve (2 bodies)",
            "3": "Three valve bodies (triple)",
            "4": "Four valve bodies (quad)",
        },
        "size_map": {"08": "8 inch", "10": "10 inch", "12": "12 inch", "14": "14 inch"},
        "pressure_map": {"L": "Low pressure 0.3 W.C.- 3.0 W.C.", "M": "Medium pressure 0.6 W.C.- 3.0 W.C."},
        "design_map": {
            "A": "Conical-shaped diffuser",
            "S": "Standard shut-off valve (metal-on-metal seal)",
            "L": "Low-leakage shut-off valve (gasketed seal)",
        },
        "control_map": {
            "H": "Rotary, low-speed electric actuator; NEMA 1; on single 8, 10, and 12 only",
            "I": "Rotary, low-speed electric actuator; IP54",
            "L": "Rotary, low-speed electric actuator; IP56",
        },
        "controller_map": {
            "A": "Theris TP Supply",
            "B": "Theris TX Supply",
            "C": "Theris SO Supply only",
            "D": "Theris EO Exhaust only",
            "Y": "Theris TX-RTN",
            "Z": "Theris TX-EXH",
            "N": "No electronics (tracking valve)",
            "E": "Theris TP Supply (analog without boosters)",
            "X": "Theris TX Supply (expanded features)",
            "O": "Theris SO Supply only",
        },
        "orientation_map": orientation_map,
        "failsafe_map": {"Z": "Fails to last position"},
        "option_map": {
            "B": "Two single square flanges mounted on both ends of single body valves",
            "F": "One single square flange",
            "M": "Module, scaling function",
            "P": "Pressure switch",
            "PSL": "Pressure switch, low limit",
            "O": "Power supply, valve-mounted, 120 V",
            "R": "Remote electronics",
            "T": "Power supply, valve-mounted, 230 V",
            "REI": "Remote electronics - indoor",
            "REO": "Remote electronics - outdoor",
            "WRE": "Weather resistant electronics",
            "SFB": "Square flanges on both ends",
            "SFX": "Square flange option",
        },
    },
    "TRACCEL": {
        "family_label": "Valve Family",
        "construction_label": "Construction",
        "bodies_label": "Bodies",
        "size_label": "Size",
        "pressure_label": "Pressure",
        "design_label": "Valve Design",
        "control_label": "Control Type",
        "controller_label": "Controller",
        "orientation_label": "Orientation",
        "failsafe_label": "Fail-Safe",
        "family_map": None,
        "construction_map": {
            "A": "Body and cone uncoated aluminum; shaft uncoated 316 stainless steel",
            "B": "Body and Cone Baked-on Phenolic Coating: PFA Coated 316 Stainless Steel Shaft.",
        },
        "bodies_map": {
            "F": "One valve body with welded circular flanges",
            "1": "Single valve body (no flange)",
            "2": "Dual valve (2 bodies)",
            "3": "Three valve bodies (triple)",
            "4": "Four valve bodies (quad)",
        },
        "size_map": {"08": "8 inch", "10": "10 inch", "12": "12 inch", "14": "14 inch"},
        "pressure_map": {"L": "Low pressure 0.3 W.C.- 3.0 W.C.", "M": "Medium pressure 0.6 W.C.- 3.0 W.C."},
        "design_map": {
            "A": "Conical-shaped diffuser",
            "S": "Standard shut-off valve (metal-on-metal seal)",
            "L": "Low-leakage shut-off valve (gasketed seal)",
        },
        "control_map": {
            "H": "Rotary, low-speed electric actuator; NEMA 1; on single 8, 10, and 12 only",
            "I": "Rotary, low-speed electric actuator; IP54",
            "L": "Linear, low-speed electric actuator; IP56",
        },
        "controller_map": {
            "A": "Traccel TP Supply",
            "B": "Traccel TX Supply",
            "C": "Traccel SO Supply only",
            "D": "Traccel EO Exhaust only",
            "P": "Programmable Traccel BACnet controller",
            "Y": "Traccel TX-RTN",
            "Z": "Traccel TX-EXH",
            "N": "No electronics (tracking exhaust valve)",
            "E": "Traccel TP Supply",
            "X": "Traccel TX Supply (expanded features)",
            "O": "Traccel SO Supply only",
        },
        "orientation_map": orientation_map,
        "failsafe_map": {"Z": "Fails to last position"},
        "option_map": {
            "B": "Two single square flanges mounted on both ends of single body valves",
            "F": "One single square flange",
            "M": "Module, scaling function",
            "P": "Pressure switch",
            "PSL": "Pressure switch, low limit",
            "O": "Power supply, valve-mounted, 120 V",
            "R": "Remote electronics",
            "T": "Power supply, valve-mounted, 230 V",
            "REI": "Remote electronics - indoor",
            "REO": "Remote electronics - outdoor",
            "WRE": "Weather resistant electronics",
            "SFB": "Square flanges on both ends",
            "SFX": "Square flange option",
        },
    },
    "BASE_UPGRADEABLE": {
        "family_label": "Valve Family",
        "construction_label": "Valve Construction",
        "bodies_label": "Valve Bodies",
        "size_label": "Valve Size",
        "pressure_label": "Flow/Pressure Operating",
        "design_label": "Valve Design",
        "control_label": "Control Type",
        "controller_label": "Valve Controller Designation",
        "orientation_label": "Valve Orientation",
        "failsafe_label": "Failsafe Position",
        "family_map": {"BEV": "Base upgradable exhaust valve", "BSV": "Base upgradable supply valve"},
        "construction_map": {
            "A": "Body and cone - uncoated aluminum; Shaft - uncoated 316 stainless steel",
            "B": "Body and cone with baked phenolic coating; PFA-coated 316 stainless steel shaft",
            "C": "Body, cone and hardware with baked phenolic/epoxy phenolic coating; PFA-coated 316 stainless steel shaft",
            "D": "Body, cone and hardware with PVDF coating; PFA-coated 316 stainless steel shaft",
        },
        "bodies_map": {
            "F": "One with welded circular flanges (Single Flanged)",
            "1": "One: Single no flange",
            "2": "Two, Dual: 10, 12, and 14-inch only",
            "3": "Three, Triple: 12 and 14-inch only",
            "4": "Four, Quad: 12 and 14-inch only",
        },
        "size_map": {"08": "8-inch, Single Only", "10": "10-inch, Single and Dual Only", "12": "12-inch", "14": "14-inch"},
        "pressure_map": {"M": 'Medium pressure: 0.6" to 3.0"', "L": 'Low pressure: 0.3" to 3.0"'},
        "design_map": {"A": "Conical shape diffuser", "L": "Low Leakage Shut-off Valve", "S": "Standard Shut-off Valve"},
        "control_map": {
            "Q": "Rotary, medium-speed electric actuator; proportional (2-10Vdc); IP54",
            "S": "Rotary, medium-speed electric actuator; proportional (0.5-10 Vdc); IP54",
            "T": "SMART, linear, high-speed electric actuator; proportional (2-10 Vdc)",
        },
        "controller_map": {"F": "Flow feedback module; no command capability", "N": "No controller"},
        "orientation_map": {"H": "Horizontal", "U": "Vertical upflow", "D": "Vertical downflow"},
        "failsafe_map": {
            "C": "Normally closed; Control Type T only",
            "O": "Normally open; Control Type T only",
            "Z": "To last position",
        },
        "option_map": {
            "EVI": "Exhaust valve with insulation and blocks",
            "IBO": "Insulation blocks only, no insulation",
            "PSL": "Pressure switch, low limit",
            "REI": "Remote electronics, indoor",
            "SFB": "Square flanges on both ends of Bodies = 1",
            "SFD": "Single square flange on discharge of Bodies = 1",
            "SFI": "Single square flange on inlet of Bodies = 1",
        },
    },
    "CSCP": {
        "family_label": "Valve Family",
        "construction_label": "Chemical Resistance",
        "bodies_label": "Bodies",
        "size_label": "Size",
        "pressure_label": "Pressure Rating",
        "design_label": "Body Design",
        "control_label": "Actuator Type",
        "controller_label": "Controller Type",
        "orientation_label": "Valve Orientation",
        "failsafe_label": "Fail-Safe Module",
        "family_map": {"PVE": "Phoenix Valve: Exhaust", "PVS": "Phoenix Valve: Supply"},
        "construction_map": {
            "A": "Class A - Uncoated Aluminum body and cone, stainless hardware",
            "B": "Class B - Heresite Coated Aluminum body and cone, stainless hardware",
            "C": "Class C - Heresite Coated Aluminum body and cone, Heresite coated hardware",
            "D": "Class D - PVDF Coated Aluminum body and cone, PVDF/Teflon coated hardware",
            "E": 'Stainless Valve Body - Class B internals; 10" or 12" Valve only; Body Design = A only',
            "F": 'Stainless Valve Body - Class C internals; 10" or 12" Valve only; Body Design = A only',
        },
        "bodies_map": {"1": "Single", "2": "Dual", "F": "Flanged"},
        "size_map": {
            "06": "6-inch",
            "08": "8-inch; Bodies = F, 1 only",
            "10": "10-inch",
            "12": "12-inch",
            "14": "14-inch",
        },
        "pressure_map": {"L": "Low: 0.1\" to 3.0\" WC; see Note 1", "M": "Medium: 0.3\" to 3.0\" WC; see Note 1"},
        "design_map": {"A": "Standard", "L": "Low leakage shut-off", "S": "Standard shut-off"},
        "control_map": {
            "C": "Constant Volume",
            "F": "Fixed",
            "H": "Rotary standard-speed electric - floating point, NEMA 1",
            "I": "Rotary standard-speed electric - floating point, IP54",
            "L": "Linear standard-speed electric actuator - floating point, IP56",
            "M": "Linear high-speed electric actuator - floating point, IP56",
            "T": "SMART linear high-speed electric actuator - proportional 2-10 Vdc",
        },
        "controller_map": {
            "B": "ACM (Actuator Control Module) without BLE (Bluetooth Low Energy); for Actuator M",
            "D": "ACM without BLE + PBC (Programmable BACnet Controller); includes both B and P; for Actuator M",
            "N": "None; for Actuator C, F, T (and I)",
            "P": "PBC — typical for low-speed tracking master valve; for Actuator H, I, L",
            "T": "Terminal strip connector (tracking valves); must link with PBC either on a valve or as standalone; for Actuator H, I, L",
        },
        "orientation_map": orientation_map,
        "failsafe_map": {"N": "None - fail to last position", "Y": "Programmable fail-safe position"},
        "protocol_map": {
            "BMT": "BACnet MS/TP — mandatory for Controller Type B",
            "500": "PBC with BACnet MS/TP with BLE (Bluetooth Low Energy)",
            "501": "PBC with BACnet MS/TP without BLE (Bluetooth Low Energy)",
            "504": "PBC with BACnet IP with BLE (Bluetooth Low Energy)",
            "505": "PBC with BACnet IP without BLE (Bluetooth Low Energy)",
        },
        "option_map": {
            "EVI": "Exhaust valve with insulation blocks and insulation; Type = PVE only",
            "IBO": "Insulation blocks only, no insulation",
            "LCL": "Low casing leakage on Design = A valves",
            "PSL": "Pressure switch, low limit",
            "PTR": "Pressure transducer",
            "REI": "Remote electronics - indoor",
            "SFB": "Square flanges on both ends of Bodies = 1",
            "SFD": "Single square flange on discharge of Bodies = 1",
            "SFI": "Single square flange on inlet of Bodies = 1",
            "SSB": "Stainless steel shaft brackets",
        },
    },
    "ANALOG": {
        "family_label": "Valve Family",
        "construction_label": "Construction",
        "bodies_label": "Bodies",
        "size_label": "Size",
        "pressure_label": "Pressure",
        "design_label": "Valve Design",
        "control_label": "Control Type",
        "controller_label": "Controller",
        "orientation_label": "Orientation",
        "failsafe_label": "Fail-Safe",
        "family_map": {"MAV": "Electronic supply valve", "EXV": "Electronic exhaust valve"},
        "construction_map": {
            "A": "Body and cone - uncoated aluminum; Shaft - uncoated 316 stainless steel",
            "B": "Body and cone with baked phenolic coating",
            "C": "Body, cone, and hardware with baked phenolic coating, PFA coated stainless steel shaft",
            "S": "Special coating and/or components",
        },
        "bodies_map": {
            "F": "One valve body with welded circular flange (single flanged)",
            "1": "One valve body (single no flange)",
            "2": "Two valve bodies (dual)",
            "3": "Three valve bodies (triple)",
            "4": "Four valve bodies (quad)",
        },
        "size_map": {
            "08": '8" valve',
            "10": '10" valve',
            "12": '12" valve',
        },
        "pressure_map": {"M": "Medium pressure 0.6 W.C.- 3.0 W.C."},
        "design_map": {"A": "Conical shape diffuser (Accel II)"},
        "control_map": {"A": "Analog/pneumatic", "E": "Analog/electric"},
        "controller_map": {
            "E": "Electronic valve with no booster valves",
            "M": "Main electronic valve with booster valves",
            "H": "Hood exhaust valve with no booster valves, includes H/I card and pressure switch",
            "I": "Hood exhaust valve with booster valves, includes H/I card and pressure switch",
            "R": "Hood exhaust valve with no booster valves, includes H/I card with alarm relay output and pressure switch",
            "Q": "Hood exhaust valve with booster valves, includes H/I card with alarm relay output and pressure switch",
            "S": "Associated (or standalone) analog valve without pneumatic solenoids",
            "P": "Associated analog valve with pneumatic solenoids",
        },
        "orientation_map": orientation_map,
        "failsafe_map_exv": {
            "O": "Normally open exhaust valve",
            "E": "Normally closed exhaust valve",
            "M": "No fail-safe exhaust valve (electric actuation only)",
        },
        "failsafe_map_mav": {
            "C": "Normally closed supply valve",
            "S": "Normally open supply valve",
            "N": "No fail-safe supply valve (electric actuation only)",
        },
        "option_map": {
            "B": "Two single square flanges mounted on both ends of single body valves",
            "F": "One single square flange",
            "M": "Module, scaling function",
            "P": "Pressure switch",
            "O": "Power supply, valve-mounted, 120 V",
            "R": "Remote electronics",
            "T": "Power supply, valve-mounted, 230 V",
            "REI": "Remote electronics - indoor",
        },
    },
}

SHARED_STANDARD_TABLE_DATA = {
    ("L", "A"): {
        "title_suffix": "Low Pressure (L) + Conical Shaped Diffuser (A)",
        "drop": '0.3" - 3.0" W.C.',
        "data": {
            "08": ("35-500", "-"),
            "10": ("50-550", "100-1100"),
            "12": ("90-1050", "180-2100"),
            "14": ("200-1400", "400-2800"),
        },
        "show_standard_note": False,
    },
    ("M", "A"): {
        "title_suffix": "Medium Pressure (M) + Conical Shaped Diffuser (A)",
        "drop": '0.6" - 3.0" W.C.',
        "data": {
            "08": ("35-700", "-"),
            "10": ("50-1000", "100-2000"),
            "12": ("90-1500", "180-3000"),
            "14": ("200-2500", "400-5000"),
        },
        "show_standard_note": False,
    },
    ("L", "S"): {
        "title_suffix": "Low Pressure (L) + Standard Shut-off (S)",
        "drop": '0.3" - 3.0" W.C.',
        "data": {
            "08": ("35-400", "-"),
            "10": ("50-450", "100-900"),
            "12": ("90-900", "180-1800"),
            "14": ("200-1000", "400-2000"),
        },
        "show_standard_note": False,
    },
    ("M", "S"): {
        "title_suffix": "Medium Pressure (M) + Standard Shut-off (S)",
        "drop": '0.6" - 3.0" W.C.',
        "data": {
            "08": ("35-600", "-"),
            "10": ("50-850", "100-1700"),
            "12": ("90-1300", "180-2600"),
            "14": ("200-1600", "400-3200"),
        },
        "show_standard_note": False,
    },
}

TABLE_DATA = {
    "CELERIS_II": SHARED_STANDARD_TABLE_DATA,
    "THERIS": SHARED_STANDARD_TABLE_DATA,
    "TRACCEL": SHARED_STANDARD_TABLE_DATA,
    "BASE_UPGRADEABLE": SHARED_STANDARD_TABLE_DATA,
    "ANALOG": {
        ("M", "A"): {
            "title": "Analog Medium Pressure (M) + Conical Shape Diffuser (A)",
            "drop": '0.6" - 3.0" W.C.',
            "data": {
                "08": ("35-700", "-"),
                "10": ("50-1000", "100-2000"),
                "12": ("90-1500", "180-3000"),
            },
            "show_standard_note": False,
        },
    },
    "CSCP": {
        ("L", "A"): {
            "title": "CSCP Low Pressure (L) + Standard Body Design (A)",
            "drop": '0.3" - 3.0" W.C.',
            "data": {"08": ("35-500", "-"), "10": ("50-550", "100-1100"), "12": ("90-1050", "180-2100"), "14": ("200-1400", "400-2800")},
            "show_standard_note": False,
        },
        ("M", "A"): {
            "title": "CSCP Medium Pressure (M) + Standard Body Design (A)",
            "drop": '0.6" - 3.0" W.C.',
            "data": {"06": ("30-350", "-"), "08": ("35-700", "-"), "10": ("50-1000", "100-2000"), "12": ("90-1500", "180-3000"), "14": ("200-2500", "400-5000")},
            "show_standard_note": False,
        },
        ("L", "S"): {
            "title": "CSCP Low Pressure (L) + Standard Shut-off (S)",
            "drop": '0.3" - 3.0" W.C.',
            "data": {"08": ("35-400", "-"), "10": ("50-450", "100-900"), "12": ("90-900", "180-1800"), "14": ("200-1000", "400-2000")},
            "show_standard_note": False,
        },
        ("M", "S"): {
            "title": "CSCP Medium Pressure (M) + Standard Shut-off (S)",
            "drop": '0.6" - 3.0" W.C.',
            "data": {"08": ("35-600", "-"), "10": ("50-850", "100-1700"), "12": ("90-1300", "180-2600"), "14": ("200-1600", "400-3200")},
            "show_standard_note": False,
        },
    },
}


def parse_dash_options(option_segments: list[str]) -> list[str]:
    return [opt.strip().upper() for opt in option_segments if opt.strip()]


def safe_char(value: str, index: int, default: str = "None") -> str:
    return value[index] if index < len(value) else default


def _normalize_str(value: str, expected_len: int, label: str, strip_spaces: bool = False) -> tuple[str, list[str]]:
    """Shared helper: validate length, pad with '?' or truncate, return (cleaned, warnings)."""
    warnings: list[str] = []
    cleaned = (value or "").strip().upper()
    if strip_spaces:
        cleaned = cleaned.replace(" ", "")
    if len(cleaned) < expected_len:
        warnings.append(f"{label} is too short ({len(cleaned)}). Expected {expected_len} characters.")
        cleaned = cleaned.ljust(expected_len, "?")
    elif len(cleaned) > expected_len:
        warnings.append(f"{label} is too long ({len(cleaned)}). Expected {expected_len} characters.")
        cleaned = cleaned[:expected_len]
    return cleaned, warnings


def normalize_suffix(raw_suffix: str, expected_len: int = 5) -> tuple[str, list[str]]:
    return _normalize_str(raw_suffix, expected_len, "Suffix")


def normalize_base(raw_base: str, expected_len: int = 8) -> tuple[str, list[str]]:
    return _normalize_str(raw_base, expected_len, "Base", strip_spaces=True)


def detect_product_line(model: str, analog_active: bool = False) -> str:
    model = model.strip().upper()
    prefix = model.split("-")[0].replace(" ", "")[:3]
    if analog_active and prefix in ("MAV", "EXV"):
        return "ANALOG"
    if prefix in ("HSV", "HEV"):
        return "THERIS"
    if prefix in ("MAV", "EXV"):
        return "CELERIS_II"
    if prefix in ("TSV", "TEV"):
        return "TRACCEL"
    if prefix in ("PVE", "PVS"):
        return "CSCP"
    if prefix in ("BEV", "BSV"):
        return "BASE_UPGRADEABLE"
    return "UNKNOWN"


def canonical_field_name(product_line: str, logical_field: str) -> str:
    config = standard_product_configs.get(product_line)
    fallback_map = {
        "family": "Valve Family",
        "construction": "Construction",
        "bodies": "Bodies",
        "size": "Size",
        "pressure": "Pressure",
        "design": "Valve Design",
        "control": "Control Type",
        "controller": "Controller",
        "orientation": "Orientation",
        "failsafe": "Fail-Safe",
        "protocol": "Communication Protocol",
        "options": "Options",
        "base": "Base",
        "suffix": "Suffix",
    }
    if not config:
        return fallback_map.get(logical_field, logical_field)
    field_map = {
        "family": config.get("family_label", "Valve Family"),
        "construction": config.get("construction_label", "Construction"),
        "bodies": config.get("bodies_label", "Bodies"),
        "size": config.get("size_label", "Size"),
        "pressure": config.get("pressure_label", "Pressure"),
        "design": config.get("design_label", "Valve Design"),
        "control": config.get("control_label", "Control Type"),
        "controller": config.get("controller_label", "Controller"),
        "orientation": config.get("orientation_label", "Orientation"),
        "failsafe": config.get("failsafe_label", "Fail-Safe"),
        "protocol": "Communication Protocol",
        "options": "Options",
        "base": "Base",
        "suffix": "Suffix",
    }
    return field_map.get(logical_field, logical_field)


def validation_field_labels(product_line: str) -> dict[str, str]:
    return {k: canonical_field_name(product_line, k) for k in [
        "family", "construction", "bodies", "size", "pressure", "design",
        "control", "controller", "orientation", "failsafe", "protocol", "options", "base", "suffix"
    ]}


def parse_model(full_model: str, analog_active: bool = False) -> tuple[bool, str, "ParsedModel | None"]:
    normalized = full_model.strip().upper()
    if not normalized:
        return False, "Model number is empty.", None

    parts = normalized.split("-")
    raw_base = parts[0] if parts else ""
    raw_suffix = parts[1] if len(parts) > 1 else ""

    base, base_warnings = normalize_base(raw_base, expected_len=8)
    product_line = detect_product_line(normalized, analog_active)
    suffix, suffix_warnings = normalize_suffix(raw_suffix, expected_len=5)

    prefix = base[0:3]
    construction = safe_char(base, 3, "?")
    qty_char = safe_char(base, 4, "?")
    size_code = base[5:7] if len(base) >= 7 else "??"
    pressure = safe_char(base, 7, "?")

    design_char = safe_char(suffix, 0, "None")
    control_type = safe_char(suffix, 1, "None")
    controller = safe_char(suffix, 2, "None")
    orientation = safe_char(suffix, 3, "None")
    failsafe = safe_char(suffix, 4, "None")

    _CSCP_PROTOCOL_CONTROLLERS = {"B", "D", "P"}
    _CSCP_KNOWN_PROTOCOLS = {"BMT", "500", "501", "504", "505"}
    if product_line == "CSCP" and safe_char(suffix, 2, "?") in _CSCP_PROTOCOL_CONTROLLERS:
        candidate = parts[2].strip().upper() if len(parts) > 2 else ""
        if candidate in _CSCP_KNOWN_PROTOCOLS:
            protocol = candidate
            options = parse_dash_options(parts[3:]) if len(parts) > 3 else []
        else:
            protocol = ""
            options = parse_dash_options(parts[2:]) if len(parts) > 2 else []
    else:
        protocol = ""
        options = parse_dash_options(parts[2:]) if len(parts) > 2 else []

    parsed_model = ParsedModel(
        full_model=normalized,
        product_line=product_line,
        base=base,
        suffix=suffix,
        prefix=prefix,
        construction=construction,
        qty_char=qty_char,
        size_code=size_code,
        pressure=pressure,
        design_char=design_char,
        control_type=control_type,
        controller=controller,
        orientation=orientation,
        failsafe=failsafe,
        protocol=protocol,
        options=options,
    )

    messages: list[str] = []
    if product_line == "UNKNOWN":
        messages.append("Unknown product prefix. Decoding attempted with partial parsing.")
    messages.extend(base_warnings)
    messages.extend(suffix_warnings)

    if messages:
        return True, " | ".join(messages), parsed_model

    return True, "Valid", parsed_model


def decode_option_list(options: list[str], mapping: dict, numeric_special: bool = False) -> str:
    if not options:
        return "None"
    decoded = []
    for option_code in options:
        if numeric_special and option_code.isdigit() and 1 <= int(option_code) <= 99:
            decoded.append(f"{option_code} -> Denotes factory-assigned special")
        else:
            decoded.append(f"{option_code} -> {mapping.get(option_code, 'Not a valid entry')}")
    return "; ".join(decoded)


def _decode_single_code(code: str, mapping: dict, allow_none: bool = True) -> str:
    if allow_none and code == "None":
        return "None"
    return f"{code} -> {mapping.get(code, 'Not a valid entry')}"


def _analog_failsafe_mapping(config: dict, prefix: str) -> dict:
    if prefix == "EXV":
        return config["failsafe_map_exv"]
    if prefix == "MAV":
        return config["failsafe_map_mav"]
    return {}


def decode_unknown_model(parsed_model: ParsedModel) -> dict[str, str]:
    return {
        "Product Line": "Unknown",
        "Valve Family": parsed_model.prefix or "Not a valid entry",
        "Construction": parsed_model.construction or "Not a valid entry",
        "Bodies": parsed_model.qty_char or "Not a valid entry",
        "Size": parsed_model.size_code or "Not a valid entry",
        "Pressure": parsed_model.pressure or "Not a valid entry",
        "Valve Design": parsed_model.design_char or "Not a valid entry",
        "Control Type": parsed_model.control_type or "Not a valid entry",
        "Controller": parsed_model.controller or "Not a valid entry",
        "Orientation": parsed_model.orientation or "Not a valid entry",
        "Fail-Safe": parsed_model.failsafe or "Not a valid entry",
        "Options": ", ".join(parsed_model.options) if parsed_model.options else "None",
    }


def _decode_with_config_labels(parsed_model: ParsedModel, config: dict) -> dict[str, str]:
    decoded_fields: dict[str, str] = {
        "Product Line": PRODUCT_DISPLAY_NAMES.get(parsed_model.product_line, parsed_model.product_line),
        config["family_label"]: (
            parsed_model.prefix
            if config["family_map"] is None
            else f"{parsed_model.prefix} -> {config['family_map'].get(parsed_model.prefix, 'Not a valid entry')}"
        ),
        config["construction_label"]: _decode_single_code(parsed_model.construction, config["construction_map"], allow_none=False),
        config["bodies_label"]: _decode_single_code(parsed_model.qty_char, config["bodies_map"], allow_none=False),
        config["size_label"]: _decode_single_code(parsed_model.size_code, config["size_map"], allow_none=False),
        config["pressure_label"]: _decode_single_code(parsed_model.pressure, config["pressure_map"], allow_none=False),
        config["design_label"]: _decode_single_code(parsed_model.design_char, config["design_map"]),
        config["control_label"]: _decode_single_code(parsed_model.control_type, config["control_map"]),
        config["controller_label"]: _decode_single_code(parsed_model.controller, config["controller_map"]),
        config["orientation_label"]: _decode_single_code(parsed_model.orientation, config["orientation_map"]),
    }

    if parsed_model.product_line == "ANALOG":
        failsafe_map = _analog_failsafe_mapping(config, parsed_model.prefix)
        decoded_fields[config["failsafe_label"]] = (
            "Unknown prefix" if not failsafe_map
            else _decode_single_code(parsed_model.failsafe, failsafe_map)
        )
        decoded_fields["Options"] = decode_option_list(parsed_model.options, config["option_map"], numeric_special=True)
        return decoded_fields

    decoded_fields[config["failsafe_label"]] = _decode_single_code(parsed_model.failsafe, config["failsafe_map"])

    if parsed_model.product_line == "CSCP":
        decoded_fields["Communication Protocol"] = (
            _decode_single_code(parsed_model.protocol, config["protocol_map"])
            if parsed_model.protocol else "None"
        )

    decoded_fields["Options"] = decode_option_list(parsed_model.options, config["option_map"])
    return decoded_fields


def decode_model(parsed_model: ParsedModel) -> dict[str, str]:
    if parsed_model.product_line not in standard_product_configs:
        return decode_unknown_model(parsed_model)
    config = standard_product_configs[parsed_model.product_line]
    return _decode_with_config_labels(parsed_model, config)


def add_validation_issue(validation_issues: list[dict], field_name: str, message: str) -> None:
    validation_issues.append({"field": field_name, "message": message})


def require_in(validation_issues: list[dict], field_name: str, actual: str, allowed: set[str], message: str) -> None:
    if actual not in allowed:
        add_validation_issue(validation_issues, field_name, message)


def validate_code_against_map(validation_issues: list[dict], field_name: str, code: str, mapping: dict, product_line: str) -> None:
    if code == "None":
        return
    if code not in mapping:
        add_validation_issue(validation_issues, field_name, f"{code} is not a valid entry for {field_name} in {product_line}.")


def validate_options_against_map(validation_issues: list[dict], options_field: str, options: list[str], mapping: dict, product_line: str, numeric_special: bool = False) -> None:
    for option_code in options:
        if numeric_special and option_code.isdigit() and 1 <= int(option_code) <= 99:
            continue
        if option_code not in mapping:
            add_validation_issue(validation_issues, options_field, f"{option_code} is not a valid option for {product_line}.")


def dedupe_validation_issues(validation_issues: list[dict]) -> list[dict]:
    seen = set()
    deduped = []
    for issue in validation_issues:
        key = (issue["field"], issue["message"])
        if key not in seen:
            seen.add(key)
            deduped.append(issue)
    return deduped


def validate_unknown_model(parsed_model: ParsedModel) -> list[dict]:
    labels = validation_field_labels(parsed_model.product_line)
    issues = [{"field": labels["family"], "message": "Unknown product prefix. Model could not be matched to a supported product line."}]
    return dedupe_validation_issues(issues)


def validate_common_codes(parsed_model: ParsedModel, validation_issues: list[dict], analog_numeric_special_options: bool = False) -> None:
    if parsed_model.product_line not in standard_product_configs:
        return

    config = standard_product_configs[parsed_model.product_line]
    labels = validation_field_labels(parsed_model.product_line)

    if config["family_map"] is not None:
        validate_code_against_map(validation_issues, labels["family"], parsed_model.prefix, config["family_map"], parsed_model.product_line)

    validate_code_against_map(validation_issues, labels["construction"], parsed_model.construction, config["construction_map"], parsed_model.product_line)
    validate_code_against_map(validation_issues, labels["bodies"], parsed_model.qty_char, config["bodies_map"], parsed_model.product_line)
    validate_code_against_map(validation_issues, labels["size"], parsed_model.size_code, config["size_map"], parsed_model.product_line)

    if "pressure_map" in config:
        validate_code_against_map(validation_issues, labels["pressure"], parsed_model.pressure, config["pressure_map"], parsed_model.product_line)

    validate_code_against_map(validation_issues, labels["design"], parsed_model.design_char, config["design_map"], parsed_model.product_line)
    validate_code_against_map(validation_issues, labels["control"], parsed_model.control_type, config["control_map"], parsed_model.product_line)
    validate_code_against_map(validation_issues, labels["controller"], parsed_model.controller, config["controller_map"], parsed_model.product_line)
    validate_code_against_map(validation_issues, labels["orientation"], parsed_model.orientation, config["orientation_map"], parsed_model.product_line)

    if parsed_model.product_line == "ANALOG":
        failsafe_map = _analog_failsafe_mapping(config, parsed_model.prefix)
        if failsafe_map:
            validate_code_against_map(validation_issues, labels["failsafe"], parsed_model.failsafe, failsafe_map, parsed_model.product_line)
    else:
        validate_code_against_map(validation_issues, labels["failsafe"], parsed_model.failsafe, config["failsafe_map"], parsed_model.product_line)

    if parsed_model.product_line == "CSCP" and parsed_model.protocol:
        validate_code_against_map(validation_issues, labels["protocol"], parsed_model.protocol, config["protocol_map"], parsed_model.product_line)

    validate_options_against_map(
        validation_issues, labels["options"], parsed_model.options, config["option_map"],
        parsed_model.product_line, numeric_special=analog_numeric_special_options,
    )


def validate_analog_rules(parsed_model: ParsedModel, validation_issues: list[dict]) -> None:
    labels = validation_field_labels(parsed_model.product_line)
    if parsed_model.pressure != "M":
        add_validation_issue(validation_issues, labels["pressure"], "Analog valves require Pressure = M (medium pressure).")


def validate_celeris_rules(parsed_model: ParsedModel, validation_issues: list[dict]) -> None:
    labels = validation_field_labels(parsed_model.product_line)

    if parsed_model.construction == "D":
        require_in(validation_issues, labels["bodies"], parsed_model.qty_char, {"F", "1"}, "Celeris II Construction D is limited to Bodies = F or 1.")
        require_in(validation_issues, labels["size"], parsed_model.size_code, {"08", "10", "12"}, "Celeris II Construction D is limited to Sizes 08, 10, and 12.")
        if any(opt in parsed_model.options for opt in ("SFB", "SFX")):
            add_validation_issue(validation_issues, labels["options"], "Celeris II Construction D cannot be ordered with SFB or SFX.")

    if parsed_model.control_type == "H":
        require_in(validation_issues, labels["bodies"], parsed_model.qty_char, {"F", "1"}, "Celeris II Control Type H is limited to single-body valves (Bodies = F or 1).")
        require_in(validation_issues, labels["size"], parsed_model.size_code, {"08", "10", "12"}, "Celeris II Control Type H is limited to Sizes 08, 10, and 12.")

    if parsed_model.controller == "H" and parsed_model.prefix != "EXV":
        add_validation_issue(validation_issues, labels["controller"], "Celeris II Controller H is an exhaust valve controller and is not valid on MAV supply valves.")

    if parsed_model.controller == "H" and parsed_model.control_type in {"H", "I", "L"}:
        add_validation_issue(validation_issues, labels["control"], "Celeris II Controller H cannot be used with low-speed actuators (Control Type H, I, or L).")


def validate_cscp_rules(parsed_model: ParsedModel, validation_issues: list[dict]) -> None:
    labels = validation_field_labels(parsed_model.product_line)

    if parsed_model.size_code == "06":
        require_in(validation_issues, labels["bodies"], parsed_model.qty_char, {"F", "1"}, "CSCP Size 06 requires Bodies = F or 1.")
        if parsed_model.pressure != "M":
            add_validation_issue(validation_issues, labels["pressure"], "CSCP Size 06 requires Pressure Rating = M.")
        if parsed_model.design_char != "A":
            add_validation_issue(validation_issues, labels["design"], "CSCP Size 06 requires Body Design = A.")
        require_in(validation_issues, labels["orientation"], parsed_model.orientation, {"H", "U"}, "CSCP Size 06 requires Valve Orientation = H or U.")

    if parsed_model.size_code == "08":
        require_in(validation_issues, labels["bodies"], parsed_model.qty_char, {"F", "1"}, "CSCP Size 08 requires Bodies = F or 1.")

    if parsed_model.construction in ("E", "F"):
        require_in(validation_issues, labels["size"], parsed_model.size_code, {"10", "12"}, f"CSCP Chemical Resistance {parsed_model.construction} is limited to Size 10 or 12.")
        if parsed_model.design_char != "A":
            add_validation_issue(validation_issues, labels["design"], f"CSCP Chemical Resistance {parsed_model.construction} requires Body Design = A.")

    if parsed_model.control_type == "C" and parsed_model.controller != "N":
        add_validation_issue(validation_issues, labels["controller"], "CSCP Actuator Type C requires Controller Type = N only.")

    if parsed_model.control_type == "F":
        if parsed_model.controller != "N":
            add_validation_issue(validation_issues, labels["controller"], "CSCP Actuator Type F requires Controller Type = N only.")
        if parsed_model.qty_char != "2":
            add_validation_issue(validation_issues, labels["bodies"], "CSCP Actuator Type F requires Bodies = 2.")
        require_in(validation_issues, labels["size"], parsed_model.size_code, {"10", "12"}, "CSCP Actuator Type F is limited to Size 10 or 12.")

    if parsed_model.control_type == "H":
        require_in(validation_issues, labels["size"], parsed_model.size_code, {"06", "08", "10", "12"}, "CSCP Actuator Type H is limited to Size 06, 08, 10, or 12.")
        require_in(validation_issues, labels["controller"], parsed_model.controller, {"P", "T"}, "CSCP Actuator Type H requires Controller Type = P or T.")

    if parsed_model.control_type == "I":
        require_in(validation_issues, labels["size"], parsed_model.size_code, {"08", "10", "12", "14"}, "CSCP Actuator Type I is limited to Size 08, 10, 12, or 14.")
        require_in(validation_issues, labels["controller"], parsed_model.controller, {"N", "P", "T"}, "CSCP Actuator Type I requires Controller Type = N, P, or T.")

    if parsed_model.control_type == "L":
        require_in(validation_issues, labels["controller"], parsed_model.controller, {"P", "T"}, "CSCP Actuator Type L requires Controller Type = P or T.")

    if parsed_model.control_type == "M":
        require_in(validation_issues, labels["controller"], parsed_model.controller, {"B", "D"}, "CSCP Actuator Type M requires Controller Type = B or D.")

    if parsed_model.control_type == "T" and parsed_model.controller != "N":
        add_validation_issue(validation_issues, labels["controller"], "CSCP Actuator Type T requires Controller Type = N only.")

    if parsed_model.controller == "B":
        if parsed_model.protocol != "BMT":
            add_validation_issue(validation_issues, labels["protocol"], "CSCP Controller Type B requires Communication Protocol = BMT.")
    elif parsed_model.controller in ("D", "P"):
        require_in(validation_issues, labels["protocol"], parsed_model.protocol, {"500", "501", "504", "505"}, "CSCP Controller Type D or P requires Communication Protocol = 500, 501, 504, or 505.")
    else:
        if parsed_model.protocol:
            add_validation_issue(validation_issues, labels["protocol"], "CSCP Communication Protocol should only be present for Controller Type B, D, or P.")

    if "EVI" in parsed_model.options and parsed_model.prefix != "PVE":
        add_validation_issue(validation_issues, labels["options"], "CSCP Option EVI is limited to Type = PVE only.")

    if "LCL" in parsed_model.options:
        if parsed_model.design_char != "A":
            add_validation_issue(validation_issues, labels["options"], "CSCP Option LCL is limited to Body Design = A.")
        require_in(validation_issues, labels["options"], parsed_model.size_code, {"08", "10", "12", "14"}, "CSCP Option LCL is limited to Sizes 08, 10, 12, or 14.")

    if "REI" in parsed_model.options and parsed_model.controller not in ("B", "D", "P"):
        add_validation_issue(validation_issues, labels["options"], "CSCP Option REI is limited to Controller Type = B, D, or P.")

    for option_code in ("SFB", "SFD", "SFI"):
        if option_code in parsed_model.options:
            if parsed_model.qty_char != "1":
                add_validation_issue(validation_issues, labels["options"], f"CSCP Option {option_code} is limited to Bodies = 1.")
            require_in(validation_issues, labels["options"], parsed_model.construction, {"A", "B", "C"}, f"CSCP Option {option_code} is limited to Chemical Resistance = A, B, or C.")

    if "SSB" in parsed_model.options:
        if parsed_model.construction != "A":
            add_validation_issue(validation_issues, labels["options"], "CSCP Option SSB is limited to Chemical Resistance = A.")
        if parsed_model.design_char != "A":
            add_validation_issue(validation_issues, labels["options"], "CSCP Option SSB requires Body Design = A.")


def validate_base_upgradeable_rules(parsed_model: ParsedModel, validation_issues: list[dict]) -> None:
    labels = validation_field_labels(parsed_model.product_line)

    if parsed_model.construction == "D":
        require_in(validation_issues, labels["bodies"], parsed_model.qty_char, {"F", "1"}, "Base Upgradeable Construction D is limited to Bodies = F or 1.")
        if parsed_model.design_char != "A":
            add_validation_issue(validation_issues, labels["design"], "Base Upgradeable Construction D requires Valve Design = A.")
        if any(opt in parsed_model.options for opt in ("SFB", "SFD", "SFI")):
            add_validation_issue(validation_issues, labels["options"], "Base Upgradeable Construction D cannot be ordered with SFB, SFD, or SFI.")

    if parsed_model.size_code == "08" and parsed_model.design_char in ("L", "S") and parsed_model.construction != "A":
        add_validation_issue(validation_issues, labels["construction"], "Base Upgradeable 8-inch shut-off valves (L or S) require Construction A.")

    if parsed_model.size_code == "14" and parsed_model.pressure == "M" and parsed_model.design_char == "L":
        add_validation_issue(validation_issues, labels["design"], "Base Upgradeable 14-inch medium pressure low leakage valves are not available.")

    if parsed_model.size_code == "14" and parsed_model.control_type in ("Q", "S") and parsed_model.qty_char not in ("F", "1"):
        add_validation_issue(validation_issues, labels["bodies"], "Base Upgradeable 14-inch valves with Control Types Q or S are only available as singles (F or 1).")

    if parsed_model.pressure == "L" and parsed_model.design_char == "L":
        add_validation_issue(validation_issues, labels["design"], "Base Upgradeable low pressure low leakage valves are not available.")

    if parsed_model.pressure == "L" and parsed_model.design_char == "S" and parsed_model.orientation == "U":
        add_validation_issue(validation_issues, labels["orientation"], "Base Upgradeable low pressure standard shut-off valves are not available as vertical up.")

    if parsed_model.control_type in ("Q", "S") and parsed_model.controller != "F":
        add_validation_issue(validation_issues, labels["controller"], "Base Upgradeable Control Types Q and S require Controller F.")

    if parsed_model.control_type == "T":
        if parsed_model.controller != "N":
            add_validation_issue(validation_issues, labels["controller"], "Base Upgradeable Control Type T requires Controller N.")
        require_in(validation_issues, labels["failsafe"], parsed_model.failsafe, {"C", "O", "Z"}, "Base Upgradeable Control Type T uses fail-safe C, O, or Z.")
    else:
        if parsed_model.failsafe in ("C", "O"):
            add_validation_issue(validation_issues, labels["failsafe"], "Base Upgradeable fail-safe C or O is only valid with Control Type T.")

    if "EVI" in parsed_model.options:
        if parsed_model.prefix != "BEV":
            add_validation_issue(validation_issues, labels["options"], "Base Upgradeable Option EVI is only available on exhaust valves (BEV).")
        if "IBO" in parsed_model.options:
            add_validation_issue(validation_issues, labels["options"], "Base Upgradeable Options EVI and IBO cannot both be ordered.")

    if "REI" in parsed_model.options:
        require_in(validation_issues, labels["options"], parsed_model.control_type, {"Q", "S"},
                   "Base Upgradeable Option REI is only valid for Control Types Q and S.")

    square_opts = [opt for opt in parsed_model.options if opt in ("SFB", "SFD", "SFI")]
    if len(square_opts) > 1:
        add_validation_issue(validation_issues, labels["options"], "Base Upgradeable SFB, SFD, and SFI cannot be ordered with each other.")

    if square_opts:
        if parsed_model.construction == "D":
            add_validation_issue(validation_issues, labels["options"], "Base Upgradeable square flange options cannot be ordered with Construction D.")
        require_in(validation_issues, labels["options"], parsed_model.qty_char, {"1"},
                   "Base Upgradeable square flange options (SFB, SFD, SFI) require Bodies = 1.")

    if parsed_model.qty_char == "2":
        require_in(validation_issues, labels["bodies"], parsed_model.size_code, {"10", "12", "14"}, "Base Upgradeable Bodies = 2 is only valid for Sizes 10, 12, and 14.")

    if parsed_model.qty_char in ("3", "4"):
        require_in(validation_issues, labels["bodies"], parsed_model.size_code, {"12", "14"}, "Base Upgradeable Bodies = 3 or 4 is only valid for Sizes 12 and 14.")

    if parsed_model.size_code == "08":
        require_in(validation_issues, labels["bodies"], parsed_model.qty_char, {"F", "1"}, "Base Upgradeable Size 08 is single only (F or 1).")

    if parsed_model.size_code == "10":
        require_in(validation_issues, labels["bodies"], parsed_model.qty_char, {"F", "1", "2"}, "Base Upgradeable Size 10 is single or dual only.")


def add_structural_validation_issues(parsed_model: ParsedModel, message: str, validation_issues: list[dict]) -> None:
    if message == "Valid":
        return

    labels = validation_field_labels(parsed_model.product_line)
    parts = [part.strip() for part in message.split("|") if part.strip()]

    for part in parts:
        if "Unknown product prefix" in part:
            add_validation_issue(validation_issues, labels["family"], part)
        elif "Base is too short" in part or "Base is too long" in part:
            add_validation_issue(validation_issues, labels["base"], part)
        elif "Suffix is too short" in part or "Suffix is too long" in part:
            add_validation_issue(validation_issues, labels["suffix"], part)


def validate_model(parsed_model: ParsedModel) -> list[dict]:
    if parsed_model.product_line == "UNKNOWN":
        return validate_unknown_model(parsed_model)

    validation_issues: list[dict] = []
    validate_common_codes(
        parsed_model,
        validation_issues,
        analog_numeric_special_options=(parsed_model.product_line == "ANALOG"),
    )

    if parsed_model.product_line == "CELERIS_II":
        validate_celeris_rules(parsed_model, validation_issues)
    elif parsed_model.product_line == "CSCP":
        validate_cscp_rules(parsed_model, validation_issues)
    elif parsed_model.product_line == "BASE_UPGRADEABLE":
        validate_base_upgradeable_rules(parsed_model, validation_issues)
    elif parsed_model.product_line == "ANALOG":
        validate_analog_rules(parsed_model, validation_issues)

    return dedupe_validation_issues(validation_issues)


def build_table(title: str, pressure_drop: str, row_data: dict[str, tuple[str, str]], show_standard_note: bool) -> str:
    lines = [
        f"\n{title} Operating Range - cfm",
        "Note: Pressure drop across valve spans all sizes (merged vertically)",
    ]
    if show_standard_note:
        lines.append("      Shared operating range note")
    lines.extend([
        "-" * 100,
        "Size    Single-body cfm range   Dual-body cfm range   Pressure Drop Across Valve",
        "------- ---------------------- ---------------------- ------------------------------",
    ])

    first = True
    for size_code, ranges in row_data.items():
        single_range, dual_range = ranges
        drop_value = pressure_drop if first else ""
        first = False
        lines.append(f'{size_code}"    {single_range:<22} {dual_range:<22} {drop_value}')

    lines.append("-" * 100)
    return "\n".join(lines) + "\n"


def _table_spec_for(parsed_model: ParsedModel) -> dict | None:
    if parsed_model.product_line not in TABLE_DATA:
        return None
    return TABLE_DATA[parsed_model.product_line].get((parsed_model.pressure, parsed_model.design_char))


def get_product_table(parsed_model: ParsedModel) -> str | None:
    table_spec = _table_spec_for(parsed_model)
    if not table_spec:
        return None

    if parsed_model.product_line in ("CELERIS_II", "THERIS", "TRACCEL", "BASE_UPGRADEABLE"):
        title = f"{PRODUCT_DISPLAY_NAMES[parsed_model.product_line]} {table_spec['title_suffix']}"
        return build_table(title, table_spec["drop"], table_spec["data"], table_spec["show_standard_note"])

    return build_table(table_spec["title"], table_spec["drop"], table_spec["data"], table_spec["show_standard_note"])


def get_product_table_structured(parsed_model: ParsedModel) -> OperatingTable | None:
    table_spec = _table_spec_for(parsed_model)
    if not table_spec:
        return None

    if parsed_model.product_line in ("CELERIS_II", "THERIS", "TRACCEL", "BASE_UPGRADEABLE"):
        title = f"{PRODUCT_DISPLAY_NAMES[parsed_model.product_line]} {table_spec['title_suffix']}"
    else:
        title = table_spec["title"]

    rows = [
        {"size": size_code, "single_cfm": single_cfm, "dual_cfm": dual_cfm, "pressure_drop": table_spec["drop"]}
        for size_code, (single_cfm, dual_cfm) in table_spec["data"].items()
    ]

    return OperatingTable(title=title, pressure_drop=table_spec["drop"], rows=rows)


def _append_product_table_note(note_lines: list[str], parsed_model: ParsedModel, include_table_text: bool) -> None:
    if not include_table_text:
        return
    table_text = get_product_table(parsed_model)
    if table_text:
        note_lines.append(table_text)


def _append_shared_weather_notes(note_lines: list[str], parsed_model: ParsedModel) -> None:
    if "REI" in parsed_model.options:
        note_lines.append(shared_notes["REI"])
    if "WRE" in parsed_model.options:
        note_lines.append(shared_notes["WRE"])


def build_analog_notes(parsed_model: ParsedModel, include_table_text: bool = True) -> list[str]:
    note_lines: list[str] = []
    note_lines.extend(analog_notes)
    _append_product_table_note(note_lines, parsed_model, include_table_text)
    return note_lines


def build_celeris_notes(parsed_model: ParsedModel, include_table_text: bool = True) -> list[str]:
    note_lines: list[str] = []
    if parsed_model.construction == "D":
        note_lines.append(notes_celerisii["D"])
    if parsed_model.controller == "H":
        note_lines.append(notes_celerisii["H_controller"])
    if "REO" in parsed_model.options:
        note_lines.append(notes_celerisii["REO"])
    if any(opt in parsed_model.options for opt in ("SFB", "SFX")):
        note_lines.append(notes_celerisii["SFB_SFX"])
    _append_shared_weather_notes(note_lines, parsed_model)
    _append_product_table_note(note_lines, parsed_model, include_table_text)
    return note_lines


def build_theris_notes(parsed_model: ParsedModel, include_table_text: bool = True) -> list[str]:
    note_lines: list[str] = []
    if parsed_model.size_code == "08":
        note_lines.append(notes_theris["08"])
    if parsed_model.size_code == "14":
        note_lines.append(notes_theris["14"])
    if parsed_model.design_char == "S" and parsed_model.pressure == "L":
        note_lines.append(notes_theris["S_low_pressure"])
    if parsed_model.design_char == "L" and parsed_model.pressure == "L":
        note_lines.append(notes_theris["L_low_pressure"])
    if "WRE" in parsed_model.options and parsed_model.controller in ("E", "O", "X"):
        note_lines.append(notes_theris["WRE_lonmark"])
    _append_shared_weather_notes(note_lines, parsed_model)
    _append_product_table_note(note_lines, parsed_model, include_table_text)
    return note_lines


def build_traccel_notes(parsed_model: ParsedModel, include_table_text: bool = True) -> list[str]:
    note_lines: list[str] = []
    _append_shared_weather_notes(note_lines, parsed_model)
    _append_product_table_note(note_lines, parsed_model, include_table_text)
    return note_lines


def build_cscp_notes(parsed_model: ParsedModel, include_table_text: bool = True) -> list[str]:
    note_lines: list[str] = ["Spare Part: CSCP VLV Enclosure — PRT-100-007-027"]
    for key in ("06", "08"):
        if parsed_model.size_code == key:
            note_lines.append(notes_cscp[key])
    for key in ("E", "F"):
        if parsed_model.construction == key:
            note_lines.append(notes_cscp[key])
    control_note_keys = {"C": "C_controller", "F": "F_controller", "H": "H_controller",
                         "I": "I_controller", "L": "L_controller", "M": "M_controller", "T": "T_controller"}
    if parsed_model.control_type in control_note_keys:
        note_lines.append(notes_cscp[control_note_keys[parsed_model.control_type]])
    for option_code in ("EVI", "LCL", "REI", "SFB", "SFD", "SFI", "SSB"):
        if option_code in parsed_model.options:
            note_lines.append(notes_cscp[option_code])
    _append_product_table_note(note_lines, parsed_model, include_table_text)
    return note_lines


def build_base_upgradeable_notes(parsed_model: ParsedModel, include_table_text: bool = True) -> list[str]:
    note_lines: list[str] = []
    if parsed_model.prefix == "BSV":
        note_lines.append("Note: Supply valves come standard with insulation and blocks.")
    if parsed_model.construction == "D":
        note_lines.append(notes_base_upgradeable["1"])
    if parsed_model.qty_char == "F":
        note_lines.append(notes_base_upgradeable["2"])
    if parsed_model.size_code == "08" and parsed_model.design_char in ("L", "S"):
        note_lines.append(notes_base_upgradeable["3"])
    if parsed_model.size_code == "14" and parsed_model.pressure == "M" and parsed_model.design_char == "L":
        note_lines.append(notes_base_upgradeable["4"])
    if parsed_model.size_code == "14" and parsed_model.control_type in ("Q", "S"):
        note_lines.append(notes_base_upgradeable["5"])
    if "PSL" in parsed_model.options:
        note_lines.append(notes_base_upgradeable["6"])
    if parsed_model.pressure == "L" and parsed_model.design_char == "L":
        note_lines.append(notes_base_upgradeable["7"])
    if parsed_model.pressure == "L" and parsed_model.design_char == "S":
        note_lines.append(notes_base_upgradeable["8"])
    if parsed_model.control_type in ("Q", "S"):
        note_lines.append(notes_base_upgradeable["9"])
    if parsed_model.control_type == "T":
        note_lines.append(notes_base_upgradeable["10"])
    if "EVI" in parsed_model.options:
        note_lines.append(notes_base_upgradeable["11"])
    if "IBO" in parsed_model.options:
        note_lines.append(notes_base_upgradeable["12"])
    if "REI" in parsed_model.options and parsed_model.control_type in ("Q", "S"):
        note_lines.append(notes_base_upgradeable["13"])
    if any(opt in parsed_model.options for opt in ("SFB", "SFD", "SFI")):
        note_lines.append(notes_base_upgradeable["14"])
    _append_product_table_note(note_lines, parsed_model, include_table_text)
    return note_lines


NOTE_BUILDERS = {
    "ANALOG": build_analog_notes,
    "CELERIS_II": build_celeris_notes,
    "THERIS": build_theris_notes,
    "TRACCEL": build_traccel_notes,
    "CSCP": build_cscp_notes,
    "BASE_UPGRADEABLE": build_base_upgradeable_notes,
}


def build_notes(parsed_model: ParsedModel, include_table_text: bool = True) -> list[str]:
    if parsed_model.product_line == "UNKNOWN":
        return []
    note_builder = NOTE_BUILDERS.get(parsed_model.product_line)
    if not note_builder:
        return []
    return list(dict.fromkeys(note_builder(parsed_model, include_table_text=include_table_text)))


def process_model(full_model: str, analog_active: bool = False) -> tuple[bool, str, dict, list, list, "ParsedModel | None"]:
    ok, message, parsed_model = parse_model(full_model, analog_active)
    if not ok or parsed_model is None:
        return False, message, {}, [], [], None

    decoded_fields = decode_model(parsed_model)
    note_lines = build_notes(parsed_model, include_table_text=True)
    validation_issues = validate_model(parsed_model)
    add_structural_validation_issues(parsed_model, message, validation_issues)
    validation_issues = dedupe_validation_issues(validation_issues)

    return True, message, decoded_fields, note_lines, validation_issues, parsed_model


def process_model_structured(
    full_model: str,
    analog_active: bool = False,
) -> tuple[bool, str, dict, list, list, "ParsedModel | None", "OperatingTable | None"]:
    ok, message, parsed_model = parse_model(full_model, analog_active)
    if not ok or parsed_model is None:
        return False, message, {}, [], [], None, None

    decoded_fields = decode_model(parsed_model)
    note_lines = build_notes(parsed_model, include_table_text=False)
    validation_issues = validate_model(parsed_model)
    add_structural_validation_issues(parsed_model, message, validation_issues)
    validation_issues = dedupe_validation_issues(validation_issues)
    operating_table = get_product_table_structured(parsed_model)

    return True, message, decoded_fields, note_lines, validation_issues, parsed_model, operating_table


# ---------------------------------------------------------------------------
# Spare Parts Infrastructure
# ---------------------------------------------------------------------------

@dataclass
class SparePartInfo:
    part_number: str
    description: str
    quantity: int = 1
    notes: list[str] = field(default_factory=list)


def _spare(part_number: str, description: str, quantity: int = 1, notes: list[str] | None = None) -> dict:
    """Convenience helper to build a spare part dict."""
    return {
        "part_number": part_number,
        "description": description,
        "quantity": quantity,
        "notes": notes or [],
    }


# ---------------------------------------------------------------------------
# Celeris II spare parts resolvers
# ---------------------------------------------------------------------------

# Board part numbers keyed by control type
_CELERIS_BOARD_BY_CONTROL: dict[str, tuple[str, str]] = {
    # control_type: (part_number, description)
    "M": ("PRT-860-100-242LF", "Celeris II Resiliency Board"),
    "H": ("PRT-860-100-143LF", "Celeris II Low Speed Board"),
    "I": ("PRT-860-100-143LF", "Celeris II Low Speed Board"),
    "L": ("PRT-860-100-143LF", "Celeris II Low Speed Board"),
    "N": ("PRT-860-100-141LF", "Celeris II Pneumatic Actuator Board"),
}


def _resolve_celeris_family_board(parsed_model: ParsedModel) -> list[dict]:
    """Return the main board spare part for a Celeris II valve based on control type."""
    entry = _CELERIS_BOARD_BY_CONTROL.get(parsed_model.control_type)
    if not entry:
        return []
    part_number, description = entry
    return [_spare(part_number, description)]


def _resolve_celeris_control_spares(parsed_model: ParsedModel) -> list[dict]:
    """Return actuator spare part for Celeris II control type M or low-speed types."""
    qty  = parsed_model.qty_char
    size = parsed_model.size_code

    # High-speed (M): single all sizes + dual 10/12 → one part; dual 14 → another
    if parsed_model.control_type == "M":
        if qty in ("F", "1"):
            return [_spare("PRT-490-000-073", "Linear High-Speed Electric Actuator (Manuf. PEM)")]
        if qty == "2":
            if size in ("10", "12"):
                return [_spare("PRT-490-000-073", "Linear High-Speed Electric Actuator (Manuf. PEM)")]
            if size == "14":
                return [_spare("PRT-490-000-092", 'Linear High-Speed Electric Actuator Dual 14" (Manuf. PEM)')]

    # Low-speed H (NEMA 1): EXV prefix, single 08/10/12 only
    if parsed_model.control_type == "H":
        if qty in ("F", "1") and size in ("08", "10", "12"):
            return [_spare("PRT-100-004-177", "Low-Speed Rotary Electric Actuator NEMA 1 (Manuf. Honeywell)")]

    # Pneumatic (N): single 08/10/12 + dual 10 → one part; dual 12 → another
    if parsed_model.control_type == "N":
        qty  = parsed_model.qty_char
        size = parsed_model.size_code
        if (qty in ("F", "1") and size in ("08", "10", "12")) or (qty == "2" and size == "10"):
            return [_spare("PRT-100-004-058", "Pneumatic Actuator (Manuf. KMC)")]
        if qty == "2" and size == "12":
            return [_spare("PRT-100-004-121", 'Pneumatic Actuator Dual 12" (Manuf. KMC)')]

    return []


def _resolve_traccel_control_spares(parsed_model: ParsedModel) -> list[dict]:
    """Return actuator spare part for Traccel low-speed control type I."""
    if parsed_model.control_type != "I":
        return []

    qty  = parsed_model.qty_char
    size = parsed_model.size_code

    # Single 08/10/12
    if qty in ("F", "1") and size in ("08", "10", "12"):
        return [_spare("PRT-100-004-157", "Low-Speed Rotary Electric Actuator IP54 (Manuf. Belimo)")]

    # Single 14 or Dual 10/12
    if (qty in ("F", "1") and size == "14") or (qty == "2" and size in ("10", "12")):
        return [_spare("PRT-100-004-174", "Low-Speed Rotary Electric Actuator IP54 Large (Manuf. Belimo)")]

    # Dual 14
    if qty == "2" and size == "14":
        return [_spare("PRT-100-004-270", 'Low-Speed Rotary Electric Actuator IP54 Dual 14" (Manuf. Belimo)')]

    return []


def _resolve_theris_control_spares(parsed_model: ParsedModel) -> list[dict]:
    """Return actuator spare part for Theris low-speed control type L."""
    if parsed_model.control_type != "L":
        return []

    qty  = parsed_model.qty_char
    size = parsed_model.size_code

    # Single all sizes + Dual 10/12
    if (qty in ("F", "1")) or (qty == "2" and size in ("10", "12")):
        return [_spare("PRT-490-000-100", "Low-Speed Linear Electric Actuator IP56 (Manuf. PEM)")]

    # Dual 14
    if qty == "2" and size == "14":
        return [_spare("PRT-490-000-095", 'Low-Speed Linear Electric Actuator IP56 Dual 14" (Manuf. PEM)')]

    return []


# Controller letter → (part_number, description) for Traccel LON
_TRACCEL_LON_CONTROLLER_PARTS: dict[str, tuple[str, str]] = {
    "O": ("PRT-860-100-161LF", "Traccel SO Room Controller, 24 VAC (LonMark)"),
    "E": ("PRT-860-100-162LF", "Traccel TP Room Controller, 24 VAC (LonMark)"),
    "X": ("PRT-860-100-163LF", "Traccel TX Room Controller, 24 VAC (LonMark)"),
}

# Controller letter → (part_number, description) for Theris LON
_THERIS_LON_CONTROLLER_PARTS: dict[str, tuple[str, str]] = {
    "O": ("PRT-860-100-164LF", "Theris SO Room Controller, 24 VAC (LonMark)"),
    "E": ("PRT-860-100-165LF", "Theris TP Room Controller, 24 VAC (LonMark)"),
    "X": ("PRT-860-100-166LF", "Theris TX Room Controller, 24 VAC (LonMark)"),
}

# Controller letter → (part_number, description) shared BACnet for both Theris + Traccel
_THERIS_TRACCEL_BACNET_CONTROLLER_PARTS: dict[str, tuple[str, str]] = {
    "A": ("PRT-860-100-193LF", "VLC-1188 TP — TP Supply (BACnet)"),
    "B": ("PRT-860-100-195LF", "VLC-1188 TX — TX Tracking Pair-Expanded (BACnet)"),
    "C": ("PRT-860-100-197LF", "VLC-1188 SO — SO Supply Only (BACnet)"),
    "D": ("PRT-860-100-198LF", "VLC-1188 EO — Exhaust Only (BACnet)"),
    "Y": ("PRT-860-100-192LF", "VLC-1188 TX-RTN — TX-RTN Tracking Triplet (BACnet)"),
    "Z": ("PRT-860-100-194LF", "VLC-1188 TX-EXH — TX Tracking Triplet Two Exhausts (BACnet)"),
}


def _resolve_theris_controller_spares(parsed_model: ParsedModel) -> list[dict]:
    """Return room controller spare part for Theris based on controller code."""
    lon_entry    = _THERIS_LON_CONTROLLER_PARTS.get(parsed_model.controller)
    bacnet_entry = _THERIS_TRACCEL_BACNET_CONTROLLER_PARTS.get(parsed_model.controller)
    entry = lon_entry or bacnet_entry
    if not entry:
        return []
    part_number, description = entry
    return [_spare(part_number, description)]


def _resolve_traccel_controller_spares(parsed_model: ParsedModel) -> list[dict]:
    """Return room controller spare part for Traccel based on controller code."""
    lon_entry    = _TRACCEL_LON_CONTROLLER_PARTS.get(parsed_model.controller)
    bacnet_entry = _THERIS_TRACCEL_BACNET_CONTROLLER_PARTS.get(parsed_model.controller)
    entry = lon_entry or bacnet_entry
    if not entry:
        return []
    part_number, description = entry
    return [_spare(part_number, description)]


def _resolve_celeris_psl_spares(parsed_model: ParsedModel) -> list[dict]:
    """Return pressure-switch spare parts for PSL option (Celeris II and CSCP)."""
    if parsed_model.product_line not in ("CELERIS_II", "CSCP") or "PSL" not in parsed_model.options:
        return []

    pressure_map = {
        "L": {
            "single": _spare("PRT-100-004-323", 'Low Pressure (.2" WC) switch assembly — Single Valve'),
            "dual":   _spare("PRT-100-004-324", 'Low Pressure (.2" WC) switch assembly — Dual Valve'),
        },
        "M": {
            "single": _spare("PRT-100-004-325", 'Medium Pressure (.3" WC) switch assembly — Single Valve'),
            "dual":   _spare("PRT-100-004-326", 'Medium Pressure (.3" WC) switch assembly — Dual Valve'),
        },
    }
    composition_map = {
        "F": [("single", 1)],
        "1": [("single", 1)],
        "2": [("dual",   1)],
        "3": [("single", 1), ("dual", 1)],
        "4": [("dual",   2)],
    }

    selected_pressure   = pressure_map.get(parsed_model.pressure)
    selected_composition = composition_map.get(parsed_model.qty_char, [])
    if not selected_pressure:
        return []

    results: list[dict] = []
    for body_type, qty in selected_composition:
        spare = selected_pressure.get(body_type)
        if spare:
            results.append({**spare, "quantity": qty})
    return results


# ---------------------------------------------------------------------------
# CSCP spare parts resolvers
# ---------------------------------------------------------------------------

def _resolve_cscp_failsafe_spares(parsed_model: ParsedModel) -> list[dict]:
    """Return FSM spare part when Fail-Safe = Y."""
    if parsed_model.failsafe == "Y":
        return [_spare("PRT-250-100-078", "CSCP Fail-Safe Module (FSM)")]
    return []


def _resolve_cscp_controller_spares(parsed_model: ParsedModel) -> list[dict]:
    """Return ACM spare part for Controller Type B or D."""
    if parsed_model.controller in ("B", "D"):
        return [_spare("PRT-250-100-076", "CSCP ACM (Actuator Control Module)")]
    return []



def resolve_field_spare_parts(parsed_model: ParsedModel, field_name: str, code: str) -> list[dict]:
    """
    Return a list of spare-part dicts for a given field + code on a parsed model.
    Each dict has keys: part_number, description, quantity, notes.
    """
    field_name = (field_name or "").strip().lower()
    code       = (code       or "").strip().upper()

    # --- Celeris II ---
    if parsed_model.product_line == "CELERIS_II":
        if field_name in {"family", "valve family"}:
            return _resolve_celeris_family_board(parsed_model)
        if field_name in {"control", "control type"} and code in {"M", "H", "I", "L", "N"}:
            return _resolve_celeris_control_spares(parsed_model)
        if field_name in {"options", "option"} and code == "PSL":
            return _resolve_celeris_psl_spares(parsed_model)

    # --- Traccel ---
    if parsed_model.product_line == "TRACCEL":
        if field_name in {"control", "control type"} and code == "I":
            return _resolve_traccel_control_spares(parsed_model)
        if field_name in {"controller", "controller type"}:
            return _resolve_traccel_controller_spares(parsed_model)

    # --- Theris ---
    if parsed_model.product_line == "THERIS":
        if field_name in {"control", "control type"} and code == "L":
            return _resolve_theris_control_spares(parsed_model)
        if field_name in {"controller", "controller type"}:
            return _resolve_theris_controller_spares(parsed_model)

    # --- CSCP ---
    if parsed_model.product_line == "CSCP":
        if field_name in {"failsafe", "fail-safe", "fail-safe module"}:
            return _resolve_cscp_failsafe_spares(parsed_model)
        if field_name in {"controller", "controller type"}:
            return _resolve_cscp_controller_spares(parsed_model)
        if field_name in {"options", "option"} and code == "PSL":
            return _resolve_celeris_psl_spares(parsed_model)

    return []


# ---------------------------------------------------------------------------
# Field popup detail builder (used by picker dialogs in the GUI)
# ---------------------------------------------------------------------------

def get_field_popup_details(parsed_model: ParsedModel, logical_field: str) -> dict:
    """
    Return a dict describing the selected code(s) and any spare parts for a
    given logical field, ready for display in a picker dialog.
    """
    logical_field = (logical_field or "").strip().lower()
    config = standard_product_configs.get(parsed_model.product_line)
    if not config:
        return {"field": logical_field, "label": logical_field, "selected_items": [], "spare_parts": []}

    # Options field — multi-value, return one entry per selected option
    if logical_field == "options":
        items = []
        for option_code in parsed_model.options:
            items.append({
                "code":        option_code,
                "description": config.get("option_map", {}).get(option_code, "Not a valid entry"),
                "spare_parts": resolve_field_spare_parts(parsed_model, "options", option_code),
            })
        return {
            "field":          "options",
            "label":          canonical_field_name(parsed_model.product_line, "options"),
            "selected_items": items,
        }

    # Single-value fields
    field_lookup: dict[str, tuple[str, dict]] = {
        "family":       (parsed_model.prefix,        config.get("family_map") or {}),
        "construction": (parsed_model.construction,  config.get("construction_map", {})),
        "bodies":       (parsed_model.qty_char,      config.get("bodies_map", {})),
        "size":         (parsed_model.size_code,     config.get("size_map", {})),
        "pressure":     (parsed_model.pressure,      config.get("pressure_map", {})),
        "design":       (parsed_model.design_char,   config.get("design_map", {})),
        "control":      (parsed_model.control_type,  config.get("control_map", {})),
        "controller":   (parsed_model.controller,    config.get("controller_map", {})),
        "orientation":  (parsed_model.orientation,   config.get("orientation_map", {})),
        "failsafe": (
            parsed_model.failsafe,
            _analog_failsafe_mapping(config, parsed_model.prefix)
            if parsed_model.product_line == "ANALOG"
            else config.get("failsafe_map", {}),
        ),
        "protocol":     (parsed_model.protocol,      config.get("protocol_map", {})),
    }

    selected_code, mapping = field_lookup.get(logical_field, ("", {}))
    return {
        "field":                logical_field,
        "label":                canonical_field_name(parsed_model.product_line, logical_field),
        "selected_code":        selected_code,
        "selected_description": mapping.get(selected_code, "Not a valid entry") if selected_code else "Not available",
        "spare_parts":          resolve_field_spare_parts(parsed_model, logical_field, selected_code),
    }


def run_baseline_debug_benchmark() -> str:
    tests = [
        ("MAVA108M-AMENZ-REI", False),
        ("EXVA108M-ANHHO-P", False),
        ("HEVA108L-SIANN-WRE", False),
        ("TEVA108L-AIPHN-REI", False),
        ("PVEA106M-AHPYN-500-REI", False),
        ("BEVA108M-AQFHZ-EVI", False),
        ("MAVA114L-ALHHZ", False),
        ("MAVD208M-AAEHN-SFB", False),
        ("BEVA108L-LQFHZ", False),
        ("BSVA108L-SQFUZ", False),
        ("PVEA106M-AHPHN-XXX-REI", False),
        ("MAVA108M-AAEHN-PSL", True),
    ]

    lines = ["=" * 80, f"{APP_NAME} - Baseline Debug Benchmark", "=" * 80]

    for model_text, analog_mode in tests:
        success, message, decoded_fields, note_lines, issues, _, operating_table = process_model_structured(model_text, analog_mode)
        lines.append(f"MODEL: {model_text} | Analog Mode: {analog_mode}")
        lines.append(f"  Success: {success}")
        lines.append(f"  Message: {message}")
        lines.append(f"  Product Line: {decoded_fields.get('Product Line', 'Unknown') if decoded_fields else 'N/A'}")
        lines.append(f"  Notes: {len(note_lines)}")
        lines.append(f"  Validation Issues: {len(issues)}")
        lines.append(f"  Operating Table Present: {operating_table is not None}")
        if issues:
            for issue in issues[:6]:
                lines.append(f"    - {issue['field']}: {issue['message']}")
        lines.append("-" * 80)

    lines.append("Baseline benchmark complete.")
    return "\n".join(lines)