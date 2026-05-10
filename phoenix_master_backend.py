# phoenix_master_backend.py
# Phoenix Master Tool backend

from dataclasses import dataclass, field

APP_NAME = "Phoenix Master Tool"

PRODUCT_DISPLAY_NAMES = {
    "CELERIS_II": "Celeris II",
    "THERIS": "Theris",
    "THERIS_FLEX": "Theris FLEX",
    "TRACCEL": "Traccel",
    "VENTURIAN": "Venturian",
    "PBC": "Programmable BACnet Controller (CSCP)",
    "FHD500": "Fume Hood Display 500 (CSCP)",
    "FHD130": "Sentry Fume Hood Display (Celeris)",
    "ZPS": "Zone Presence Sensor",
    "UPGRADE_KIT": "Valve Upgrade Kit",
    "CSCP": "CSCP",
    "BASE_UPGRADEABLE_TIERED": "Base Upgradeable (Tiered Solutions)",
    "BASE_UPGRADEABLE_CV": "Constant Volume / Base Upgradeable",
    "ANALOG": "Analog",
    "UNKNOWN": "Unknown",
}

@dataclass
class ParsedModel:
    """Parsed model data shared across all product schemas.

    Valve schemas populate the named fields below (construction, bodies,
    size, etc.). Non-valve schemas (PBC, FHD, ZPS, Upgrade Kits) leave
    most of those empty and use the schema-specific extras at the bottom.
    """
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
    # Schema-specific fields populated by non-valve parsers.
    schema: str = "valve"        # which schema parsed this model
    series: str = ""             # PBC series, FHD series, ZPS series
    function: str = ""           # PBC function (GEN/ZBH/ZBL)
    language: str = ""           # Sentry FHD language (ENG/FRC)
    module_count: str = ""       # ZPS module count (10/20/30/40)
    existing_type: str = ""      # Upgrade kit existing-valve type (BC1/BCA/...)

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

notes_base_upgradeable_tiered = {
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
        # Constructions per PDS p.12 (MKT-0006 Rev F): A, B, C, D.
        # Construction D is restricted by Note 1 (single body, no SFB/SFX, sizes 08/10/12).
        "construction_map": {
            "A": "Body and cone uncoated aluminum; uncoated 316 stainless steel shaft",
            "B": "Body and cone with baked-on phenolic coating; PFA-coated 316 stainless steel shaft",
            "C": "Body and cone with baked-on phenolic coating; hardware with titanium or baked-on epoxy phenolic coating; PFA-coated 316 stainless steel shaft",
            "D": "Body and cone with PVDF coating; hardware with PVDF or baked-on epoxy phenolic coating; PFA-coated 316 stainless steel shaft; see Note 1",
        },
        # Per PDS p.12: Bodies are F, 1, 2 only — no triple/quad on Celeris II.
        # Bodies = 2 documented as "10\", 12\", and 14\" only".
        "bodies_map": {
            "F": "Single valve body with welded circular flange",
            "1": "One valve body, no flange",
            "2": "Two valve bodies (dual); 10\", 12\", and 14\" only",
        },
        "size_map": {"08": "8 inch", "10": "10 inch", "12": "12 inch", "14": "14 inch"},
        # Per PDS p.12: Celeris II is Medium pressure only.
        "pressure_map": {"M": "Medium pressure operation; 0.3-3.0\" WC (75-750 Pa); see Note 6"},
        # Per PDS p.12: Design is Conical-shaped diffuser only.
        "design_map": {
            "A": "Conical-shaped diffuser",
        },
        "control_map": {
            "H": "Rotary, low-speed electric actuator; NEMA 1; on single 8\", 10\", and 12\" valves only",
            "I": "Rotary, low-speed electric actuator; IP54",
            "L": "Linear, low-speed electric actuator; IP56",
            "M": "Linear, high-speed electric actuator; IP56",
            "N": "Linear, pneumatic actuator",
        },
        "controller_map": {
            "E": "Electronic controller",
            "H": "Hood exhaust valve with pressure switch; see Note 2",
        },
        "orientation_map": orientation_map,
        "failsafe_map": {"C": "Normally closed", "O": "Normally opened", "Z": "Fails to last position"},
        # Per PDS p.12: 11 documented options. The previous code carried legacy
        # codes (B, F, M, P, O, R, T) that aren't in the published ordering guide.
        "option_map": {
            "EVI": "Exhaust valve with insulation blocks and insulation",
            "FHA": "Factory-mounted fan static reset kit",
            "IBO": "Insulation blocks only, no insulation",
            "LCL": "Low casing leakage",
            "PSL": "Pressure switch, low limit",
            "REI": "Remote electronics - indoor applications only; see Note 3",
            "REO": "Remote electronics - outdoor applications only, for pneumatic actuation only; see Note 4",
            "WRE": "Weather resistant electronics - outdoor applications, for electric actuation only; see Note 5",
            "SFB": "Square flanges on both ends of single-body valves; see Note 1",
            "SFX": "Single square flange mounted on either the exhaust inlet or supply discharge; see Note 1",
            "SSB": "Stainless steel shaft brackets instead of galvaneal; Chemical Resistance = A or Body Design = A only",
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
        # Theris is offered in Construction A only per MKT-0228 / MKT-0118.
        "construction_map": {
            "A": "Body and cone uncoated aluminum; shaft uncoated 316 stainless steel",
        },
        # Theris bodies are F, 1, 2 only per MKT-0228 / MKT-0118 — no triple/quad.
        # Bodies = 2 is restricted to sizes 10/12/14 (enforced in validate_theris_rules).
        "bodies_map": {
            "F": "One valve body with welded circular flanges",
            "1": "Single valve body (no flange)",
            "2": "Two valve bodies (dual); 10\", 12\", and 14\" only",
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
        # Per MKT-0228: 7 BACnet-side options, plus WRE for LonMark only.
        # WRE → LonMark constraint enforced in validate_theris_rules.
        "option_map": {
            "EVI": "Exhaust valve with insulation and blocks",
            "IBO": "Insulation blocks only, no insulation",
            "PSL": "Pressure switch, low limit",
            "REI": "Remote electronics, indoor",
            "SFB": "Square flanges on both ends of Bodies = 1",
            "SFD": "Single square flange on discharge of Bodies = 1",
            "SFI": "Single square flange on inlet of Bodies = 1",
            "WRE": "Weather resistant electronics (LonMark valves only)",
        },
    },
    # Theris FLEX per PDS p.24 (MKT-0006 Rev F).
    # Single-body only, sizes 06/08/10, family-specific controller restrictions.
    "THERIS_FLEX": {
        "family_label": "Valve Family",
        "construction_label": "Construction Class",
        "bodies_label": "Bodies",
        "size_label": "Size",
        "pressure_label": "Pressure Range",
        "design_label": "Design",
        "control_label": "Control Type",
        "controller_label": "BACnet Controller Designation",
        "orientation_label": "Orientation",
        "failsafe_label": "Fail-Safe Position",
        "family_map": {
            "FEV": "Flex exhaust valve; see Note 1",
            "FSV": "Flex supply valve (comes standard with insulation unless IBO); see Notes 2, 3",
        },
        "construction_map": {
            "A": "For clean air environments",
        },
        "bodies_map": {
            "1": "One — single, no flange",
        },
        # Size 06 has restrictions (Note 4) — no Range L, no Orientation D.
        "size_map": {
            "06": "6-inch, outer diameter 5.83\" (148 mm); see Note 4",
            "08": "8-inch, outer diameter 7.88\" (200 mm)",
            "10": "10-inch, outer diameter 9.88\" (251 mm)",
        },
        "pressure_map": {
            "M": "Medium - 0.6\" to 3.0\" WC (150 to 750 Pa)",
            "L": "Low - 0.3\" to 3.0\" WC (75 to 750 Pa)",
        },
        "design_map": {
            "A": "Standard",
        },
        "control_map": {
            "H": "Rotary low-speed electric actuator - floating point, NEMA 1",
            "L": "Linear low-speed electric actuator - floating point, IP56",
        },
        "controller_map": {
            "A": "TP - controlling supply of tracking pair",
            "C": "SO - temperature and occupancy control; see Note 5",
            "D": "EO - local flow control; see Note 5",
            "N": "None - tracking exhaust in pair",
            "V": "LM - linearization module; see Notes 5, 6",
        },
        "orientation_map": {"H": "Horizontal", "U": "Vertical up", "D": "Vertical down"},
        "failsafe_map": {"Z": "Last position"},
        "option_map": {
            "EVI": "Exhaust valve with insulation and blocks; see Note 7",
            "IBO": "Insulation blocks only, no insulation; see Note 8",
            "PSL": "Pressure switch - low limit; see Note 9",
            "REI": "Remote electronics - indoor; see Note 10",
            "SFB": "Square flanges on both ends of Bodies = 1; see Note 11",
            "SFD": "Single square flange on discharge of Bodies = 1; see Note 11",
            "SFI": "Single square flange on inlet of Bodies = 1; see Note 11",
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
            "B": "Body and cone with baked-on phenolic coating; PFA-coated 316 stainless steel shaft",
        },
        # Traccel bodies are F, 1, 2 only per MKT-0242 / MKT-0041 — no triple/quad.
        # Bodies = 2 is restricted to sizes 10/12/14 (enforced in validate_traccel_rules).
        "bodies_map": {
            "F": "One valve body with welded circular flanges",
            "1": "Single valve body (no flange)",
            "2": "Two valve bodies (dual); 10\", 12\", and 14\" only",
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
        # Per MKT-0242: 7 BACnet-side options, plus WRE for LonMark only.
        # WRE → LonMark constraint enforced in validate_traccel_rules.
        "option_map": {
            "EVI": "Exhaust valve with insulation and blocks",
            "IBO": "Insulation blocks only, no insulation",
            "PSL": "Pressure switch, low limit",
            "REI": "Remote electronics, indoor",
            "SFB": "Square flanges on both ends of Bodies = 1",
            "SFD": "Single square flange on discharge of Bodies = 1",
            "SFI": "Single square flange on inlet of Bodies = 1",
            "WRE": "Weather resistant electronics (LonMark valves only)",
        },
    },
    # Venturian Airflow Control Valves per PDS p.31 (MKT-0006 Rev F).
    "VENTURIAN": {
        "family_label": "Valve Family",
        "construction_label": "Valve Construction",
        "bodies_label": "Number of Valve Bodies",
        "size_label": "Valve Size",
        "pressure_label": "Flow/Pressure Operating Range",
        "design_label": "Valve Design",
        "control_label": "Control Type",
        "controller_label": "Valve Controller Designation",
        "orientation_label": "Valve Orientation",
        "failsafe_label": "Fail-Safe Position",
        "family_map": {
            "VEV": "Venturian Exhaust Valve",
            "VSV": "Venturian Supply Valve (insulation standard); see Note 1",
        },
        "construction_map": {
            "A": "For supply, return, and general exhaust applications; see Note 2",
        },
        "bodies_map": {
            "F": "One — single flanged (welded circular flanges); see Notes 3, 13",
            "1": "One — single, no flange",
            "2": "Two — Dual; 10\", 12\", 14\" only; see Notes 9, 13",
        },
        "size_map": {
            "08": "8\" valve — single body only; 7.88\" (200 mm) outer diameter",
            "10": "10\" valve; 9.88\" (251 mm) outer diameter",
            "12": "12\" valve; 11.88\" (302 mm) outer diameter",
            "14": "14\" valve; 13.88\" (352 mm) outer diameter; see Note 9",
        },
        "pressure_map": {
            "M": "Medium pressure: 0.6\" to 3.0\" WC; see Note 5",
            "L": "Low pressure: 0.3\" to 3.0\" WC; see Notes 5, 6",
        },
        "design_map": {
            "A": "Standard conical-shaped diffuser; see Note 7",
            "S": "Standard shut-off; see Notes 2, 6",
        },
        "control_map": {
            "C": "Constant volume; see Notes 7, 8",
            "H": "Rotary low-speed electric; floating point; NEMA; see Note 10",
            "L": "Linear low-speed electric actuator; floating point; IP67; see Note 9",
        },
        "controller_map": {
            "A": "Analog Linearization Module; see Notes 15, 16",
            "B": "BACnet or local flow control [EO]; see Note 15",
            "C": "BACnet with temperature and occupancy control [SO]; see Notes 15, 17",
            "D": "BACnet controlling valve for tracking pair [TP]; see Notes 17, 18",
            "N": "No controller (CV valves and tracking valves); see Note 14",
        },
        "orientation_map": {
            "H": "Horizontal",
            "U": "Vertical up; see Note 6",
            "D": "Vertical down; single only (Note 4)",
        },
        "failsafe_map": {"Z": "To-last-position or not applicable; see Note 8"},
        "option_map": {
            "EVI": "Exhaust valve with insulation and blocks; see Notes 1, 11",
            "IBO": "Insulation blocks only, no insulation; see Notes 1, 12",
            "PSL": "Pressure Switch, Low limit; see Note 5",
            "SFB": "Square flange on both ends; see Note 13",
            "SFD": "Square flange on discharge of single-body valve; see Note 13",
            "SFI": "Square flange on inlet of single-body valve; see Note 13",
        },
    },
    "BASE_UPGRADEABLE_TIERED": {
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
    # Constant Volume / Base Upgradeable per PDS p.34 (MKT-0006 Rev F).
    # Same physical valve family as Tiered Solutions (BSV/BEV) but with the
    # CV-specific control types and the additional CSV/CEV families. Detection
    # routes BSV/BEV here when the control type is C/B/F/H/I/L/Z.
    "BASE_UPGRADEABLE_CV": {
        "family_label": "Valve Family",
        "construction_label": "Valve Construction",
        "bodies_label": "Number of Valve Bodies",
        "size_label": "Valve Size",
        "pressure_label": "Flow/Pressure Operating",
        "design_label": "Valve Design",
        "control_label": "Control Type",
        "controller_label": "Valve Controller Designation",
        "orientation_label": "Valve Orientation",
        "failsafe_label": "Fail-Safe Position",
        "family_map": {
            "CSV": "Constant volume supply valve (Design A only); see Note 1",
            "CEV": "Constant volume exhaust valve (Design A only); see Note 1",
            "BSV": "Base upgradable supply valve (comes standard with insulation)",
            "BEV": "Base upgradable exhaust valve",
        },
        "construction_map": {
            "A": "Body and cone uncoated aluminum; uncoated 316 stainless steel shaft",
            "B": "Body and cone with baked-on phenolic coating; PFA-coated 316 stainless steel shaft",
            "C": "Body, cone, and hardware with baked-on phenolic coating; PFA-coated 316 stainless steel shaft",
            "D": "Body and cone with PVDF coating; hardware with baked-on phenolic or PVDF coating; PFA-coated 316 stainless steel shaft; see Note 2",
        },
        "bodies_map": {
            "F": "One valve body with welded circular flanges",
            "1": "One valve body, no flange",
            "2": "Two valve bodies (dual)",
            "3": "Three valve bodies (triple)",
            "4": "Four valve bodies (quad)",
        },
        "size_map": {
            "08": "8\" valve (7.88\"/200mm); see Note 3",
            "10": "10\" valve (9.67\"/246mm)",
            "12": "12\" valve (11.84\"/301mm)",
            "14": "14\" valve (13.88\"/353mm); see Notes 4, 5",
        },
        "pressure_map": {
            "M": "Medium pressure: 0.6\" to 3.0\" WC; see Notes 4, 6",
            "L": "Low pressure: 0.3\" to 3.0\" WC; see Notes 6, 7, 8",
        },
        "design_map": {
            "A": "Conical-shaped diffuser",
            "S": "Standard Shut-off Valve; see Notes 2, 3, 7, 9",
            "L": "Low Leakage Shut-off Valve; see Notes 2, 3, 4, 6, 9",
        },
        "control_map": {
            "C": "Constant volume",
            "B": "Base upgradable pneumatic; BxV only — see Note 5",
            "F": "Fixed, field-adjustable; BxV only — see Note 5",
            "H": "Rotary, low-speed electric; floating point; NEMA 1; BxV single 8\", 10\", 12\" only — see Note 8",
            "I": "Rotary, low-speed electric; floating point; IP54; BxV only — see Note 9",
            "L": "Linear, low-speed electric; floating point; IP56; BxV only — see Note 8",
            "Z": "Rotary, low-speed electric; proportional (2-10 Vdc); IP54; BxV only — see Note 9",
        },
        "controller_map": {
            "N": "No electronics",
            "F": "Flow feedback in small black box; see Notes 8, 9",
        },
        "orientation_map": {"H": "Horizontal", "U": "Vertical upflow; see Note 7", "D": "Vertical downflow"},
        "failsafe_map": {
            "C": "Normally closed; only available for BxV with Control Type = B",
            "O": "Normally open; only available for BxV with Control Type = B",
            "Z": "Fails to last position; not available for BxV with Control Type = B",
        },
        "option_map": {
            "EVI": "Exhaust valve with insulation blocks and insulation",
            "IBO": "Valve with insulation blocks only, no insulation",
            "PSL": "Pressure switch, low limit (0.3\" WC)",
            "REI": "Remote electronics (indoor); BxV must have flow feedback (Controller = F); see Note 10",
            "REO": "Remote electronics (outdoor) for pneumatic actuators only; see Note 11",
            "SFB": "Square flanges on both ends of Bodies = 1; see Notes 2, 12",
            "SFD": "Single square flange on discharge of Bodies = 1; see Notes 2, 12",
            "SFI": "Single square flange on inlet of Bodies = 1; see Notes 2, 12",
            "SHA": "High wattage solenoid valve, 24 Vdc; controlled by a non-Phoenix device",
            "SHD": "High wattage solenoid valve, 24 Vdc; controlled by a non-Phoenix device",
            "VPO": "Power supply, valve-mounted, 120 Vac to +/- 15 Vdc; Control Type = B or F only; see Note 13",
            "VPT": "Power supply, valve-mounted, 230 Vac to +/- 15 Vdc; Control Type = B or F only; see Note 13",
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
    # ── Non-valve product lines (PDS p.11, p.56, p.57, p.58, p.54) ─────────
    # These use schemas different from the valve schema; their parsers fill
    # `series`, `function`, `language`, `module_count`, etc., and leave the
    # valve-specific fields blank.
    "PBC": {
        "schema": "pbc",
        "family_label": "Type",
        "series_label": "Series",
        "function_label": "Function",
        "family_map": {"PBC": "Programmable BACnet Controller"},
        "series_map": {
            "500": "BACnet MS/TP with BLE (Bluetooth Low Energy)",
            "501": "BACnet MS/TP without BLE (Bluetooth Low Energy)",
            "504": "BACnet IP with BLE (Bluetooth Low Energy)",
            "505": "BACnet IP without BLE (Bluetooth Low Energy)",
        },
        "function_map": {
            "GEN": "Generic - programmable logic and I/O control module",
            "ZBH": "Zone Balance High Speed - up to 20 ACMs and 10 FHDs",
            "ZBL": "Zone Balance Standard Speed - up to 4 standard speed valves directly wired to the PBC",
        },
    },
    "FHD500": {
        "schema": "fhd500",
        "family_label": "Product Family",
        "series_label": "Network/Protocol",
        "options_label": "Options",
        # FHD500 is the fume-hood display for the CSCP valve platform.
        "family_map": {"FHD": "Fume Hood Display (CSCP platform)"},
        "series_map": {"500": "BACnet MS/TP with BLE (Bluetooth Low Energy)"},
        "option_map": {
            "DHV": "DHV Interface card in enclosure",
            "HV":  "Fume Hood HV (PCA)",
            "HUB": "Fume Hood HUB - enclosure and PCB; DHV NOT included",
            "HUV": "Fume Hood HUB with DHV included",
            "RD1": "Retrofit stainless surface plate to cover FHD1xx recess mounting holes",
            "RM1": "Retrofit stainless surface plate to cover FHMx00 and FHMx10 recess mounting holes",
            "RM3": "Retrofit stainless surface plate to cover FHMx30 recess mounting holes",
        },
    },
    "FHD130": {
        "schema": "fhd130",
        "family_label": "Product Family",
        "series_label": "Series",
        "language_label": "Language",
        "options_label": "Options",
        # Sentry FHD (FHD130) is the fume-hood display for the Celeris valve platform.
        "family_map": {"FHD": "Sentry Fume Hood Display (Celeris platform)"},
        "series_map": {"130": "Sentry: Safety, FV, and Energy display"},
        "language_map": {"ENG": "English", "FRC": "French Canadian"},
        "option_map": {
            "DHV": "Digital horizontal/vertical sash interface card in the hood control hub; see Note 3",
            "HUB": "Fume hood hub - enclosure and interconnect PCB",
            "FHV": "FHD interface card; see Notes 4, 5",
            "RD1": "Recess mounting kit for FHD 1x0",
            "RM1": "Retrofit recess mounting kit for FHMx00/FHMx10",
            "RM3": "Retrofit recess mounting kit for FHMx30/FHMx31",
        },
    },
    "ZPS": {
        "schema": "zps",
        "family_label": "Product Family",
        "series_label": "Series",
        "module_count_label": "Number of Modules",
        "family_map": {"ZPS": "Zone Presence Sensor"},
        "series_map": {"3": "Series 3"},
        "module_count_map": {
            "10": "Kit with 1 ZPS unit and mounting hardware",
            "20": "Kit with 2 ZPS units and mounting hardware",
            "30": "Kit with 3 ZPS units and mounting hardware",
            "40": "Kit with 4 ZPS units and mounting hardware",
        },
    },
    "UPGRADE_KIT": {
        "schema": "upgrade_kit",
        "family_label": "Valve Family",
        "construction_label": "Valve Construction",
        "bodies_label": "Number of Valve Bodies",
        "size_label": "Valve Size",
        "pressure_label": "Flow/Pressure Operating",
        "design_label": "Valve Design",
        "control_label": "Control Type",
        "controller_label": "Valve Controller Designation",
        "orientation_label": "Valve Orientation",
        "failsafe_label": "Fail-Safe Position",
        "existing_type_label": "Existing Valve Type",
        "family_map": {
            "C2U": "Celeris 2 Upgrade; see Note 1",
            "TXU": "Traccel Upgrade; see Notes 1, 2, 9",
        },
        "construction_map": {"X": "Mandatory placeholder"},
        "bodies_map": {
            "1": "One valve body (single); see Notes 3, 4, 5",
            "2": "Two valve bodies (dual) - 10\", 12\", 14\" only; see Notes 3, 6, 7, 8",
        },
        "size_map": {
            "08": "8\" valve - single only",
            "10": "10\" valve - single and dual",
            "12": "12\" valve - single and dual",
            "14": "14\" valve - single and dual; see Note 9",
        },
        "pressure_map": {
            "M": "Medium pressure: 0.6\" to 3.0\" WC",
            "L": "Low pressure: 0.3\" to 3.0\" WC",
        },
        "design_map": {"X": "Mandatory placeholder"},
        "control_map": {
            "I": "Floating Point IP54 electric actuator with fail-to-last position; see Notes 10, 11",
            "M": "Digital high-speed electric - C2 only",
            "N": "Digital pneumatic - C2 only; see Note 12",
        },
        "controller_map": {
            "E": "C2 electronic controller; see Note 13",
            "H": "C2 hood exhaust valve with pressure switch; see Notes 10, 13, 14",
            "I": "BACnet INDIVIDUAL only; see Note 15",
            "L": "BACnet LINKED controlling; see Note 16",
            "N": "No electronics (Traccel Tracking Valve)",
            "X": "LonMARK Electronic Valve - tracking pair with expanded features; see Note 17",
        },
        "orientation_map": {"X": "Mandatory placeholder"},
        "failsafe_map": {
            "C": "Normally closed - C2 only; see Note 11",
            "O": "Normally open - C2 only; see Note 11",
            "Z": "Not applicable; see Note 12",
        },
        "existing_type_map": {
            "BC1": "FROM Single with Base Channel: All Vintages",
            "BCA": "FROM Dual with Base Channel: Vintage A",
            "BCB": "FROM Dual with Base Channel: Vintage B",
            "BCC": "FROM Dual with Base Channel: Vintage C",
            "BCD": "FROM Dual with Base Channel: Vintage D",
            "BCE": "FROM Dual with Base Channel: Vintage E",
            "NB1": "FROM Single no Base Channel: All Vintages",
            "NBF": "FROM Dual no Base Channel: Vintage F",
            "NBG": "FROM Dual no Base Channel: Vintage G",
        },
        "option_map": {"VPL": "Pressure switch, low limit; see Note 14"},
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
    "BASE_UPGRADEABLE_TIERED": SHARED_STANDARD_TABLE_DATA,
    "BASE_UPGRADEABLE_CV": SHARED_STANDARD_TABLE_DATA,
    # Venturian shares the standard valve operating ranges (PDS p.32).
    "VENTURIAN": SHARED_STANDARD_TABLE_DATA,
    # Theris FLEX has a smaller operating range table (PDS p.24).
    # Single-body only, sizes 08 and 10. Size 06 not shown in PDS table —
    # tracked in deferred-items list pending CFM data confirmation.
    "THERIS_FLEX": {
        ("M", "A"): {
            "title_suffix": "Medium Pressure (M) + Standard Design (A)",
            "drop": '0.6" - 3.0" W.C.',
            "data": {
                "08": ("70-700", "-"),
                "10": ("100-1000", "-"),
            },
            "show_standard_note": False,
        },
        ("L", "A"): {
            "title_suffix": "Low Pressure (L) + Standard Design (A)",
            "drop": '0.3" - 3.0" W.C.',
            "data": {
                "08": ("70-500", "-"),
                "10": ("100-550", "-"),
            },
            "show_standard_note": False,
        },
    },
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


def safe_char(value: str, index: int, default: str = "?") -> str:
    """Return value[index] or `default` ("?" sentinel by convention) when index is OOB.

    Callers historically passed default="None" for suffix positions, but base/suffix
    are always normalized to a fixed length first, so the default is in practice
    unreachable. Keep "?" as the standard sentinel and treat any "?" in a decoded
    field as "input was missing or invalid here."
    """
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
    parts = model.split("-")
    prefix = parts[0].replace(" ", "")[:3]

    # Non-valve schemas — short prefix-based dispatch BEFORE the valve table
    # because some prefixes (FHD, ZPS, PBC) overlap nothing in the valve set
    # but their formats differ from the valve schema.
    if prefix == "PBC":
        return "PBC"
    if prefix == "ZPS":
        return "ZPS"
    if prefix == "FHD":
        first_segment = parts[0].replace(" ", "")
        # FHD500 (network protocol series) vs FHD130 (Sentry display series)
        if first_segment.startswith("FHD500"):
            return "FHD500"
        if first_segment.startswith("FHD130") or first_segment.startswith("FHD1"):
            return "FHD130"
        return "FHD500"  # default to the BACnet series for bare "FHD"
    if prefix in ("C2U", "TXU"):
        return "UPGRADE_KIT"
    # Suffix is the 2nd dash-separated segment; the 2nd character of the
    # suffix is the Control Type, which is the only field that can
    # distinguish Tiered Solutions (controls Q/S/T) from CV/BxV (controls
    # C/B/F/H/I/L/Z) when the prefix is BSV/BEV.
    suffix = parts[1].replace(" ", "") if len(parts) > 1 else ""
    control = suffix[1] if len(suffix) > 1 else ""

    if analog_active and prefix in ("MAV", "EXV"):
        return "ANALOG"
    if prefix in ("HSV", "HEV"):
        return "THERIS"
    if prefix in ("FSV", "FEV"):
        return "THERIS_FLEX"
    if prefix in ("MAV", "EXV"):
        return "CELERIS_II"
    if prefix in ("TSV", "TEV"):
        return "TRACCEL"
    if prefix in ("VSV", "VEV"):
        return "VENTURIAN"
    if prefix in ("PVE", "PVS"):
        return "CSCP"
    if prefix in ("CSV", "CEV"):
        # Constant Volume valves only exist on the CV/BxV ordering matrix.
        return "BASE_UPGRADEABLE_CV"
    if prefix in ("BEV", "BSV"):
        # Q/S/T are the Tiered control types (PDS p.45). Anything else
        # routes to CV/BxV (PDS p.34). Empty suffix or unknown control falls
        # through to Tiered as the historical default.
        if control in ("C", "B", "F", "H", "I", "L", "Z"):
            return "BASE_UPGRADEABLE_CV"
        return "BASE_UPGRADEABLE_TIERED"
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


def _schema_for(product_line: str) -> str:
    """Return which schema's parser handles a given product line.

    Valve schema covers all the legacy ordering matrices (CSCP, Celeris,
    Theris, Theris FLEX, Traccel, Venturian, BxV variants, Analog).
    Non-valve schemas are simpler accessory products with their own format.
    """
    return _PRODUCT_LINE_SCHEMA.get(product_line, "valve")


# Mapping is filled in lazily — Phase E sets up the dispatch table; Phases
# F-J add new product lines and append to it.
_PRODUCT_LINE_SCHEMA: dict[str, str] = {
    "PBC": "pbc",
    "FHD500": "fhd500",
    "FHD130": "fhd130",
    "ZPS": "zps",
    "UPGRADE_KIT": "upgrade_kit",
}


def parse_model(full_model: str, analog_active: bool = False) -> tuple[bool, list[dict], "ParsedModel | None"]:
    """Parse a model number into a ParsedModel and structural warnings.

    Top-level dispatcher. Detects the product line by prefix, picks a
    schema, and delegates to the matching parser. The "valve" schema
    handles the standard `[base]-[suffix]-[protocol]-[options]` shape
    used by every traditional Phoenix valve. Non-valve schemas (PBC,
    FHD, ZPS, Upgrade Kits) have their own parsers.

    Each warning is a dict ``{"logical_field": str, "message": str}``;
    the GUI uses ``validation_field_labels`` to translate the logical
    field name into a product-specific display label.
    """
    normalized = full_model.strip().upper()
    if not normalized:
        return False, [{"logical_field": "base", "message": "Model number is empty."}], None

    product_line = detect_product_line(normalized, analog_active)
    schema = _schema_for(product_line)

    if schema == "valve":
        return _parse_valve_schema(normalized, product_line)
    if schema == "pbc":
        return _parse_pbc_schema(normalized, product_line)
    if schema == "fhd500":
        return _parse_fhd500_schema(normalized, product_line)
    if schema == "fhd130":
        return _parse_fhd130_schema(normalized, product_line)
    if schema == "zps":
        return _parse_zps_schema(normalized, product_line)
    if schema == "upgrade_kit":
        return _parse_upgrade_kit_schema(normalized, product_line)
    return _parse_valve_schema(normalized, product_line)


def _parse_valve_schema(normalized: str, product_line: str) -> tuple[bool, list[dict], "ParsedModel | None"]:
    """Parse a model number using the standard valve schema:
       ``[3-char prefix][construction][bodies][size 2-digit][pressure]
        - [design][control][controller][orientation][failsafe]
        - [protocol]                       (CSCP only, optional)
        - [option, option, ...]``
    """
    parts = normalized.split("-")
    raw_base = parts[0] if parts else ""
    raw_suffix = parts[1] if len(parts) > 1 else ""

    base, base_warnings = normalize_base(raw_base, expected_len=8)
    suffix, suffix_warnings = normalize_suffix(raw_suffix, expected_len=5)

    prefix = base[0:3]
    construction = safe_char(base, 3)
    qty_char = safe_char(base, 4)
    size_code = base[5:7] if len(base) >= 7 else "??"
    pressure = safe_char(base, 7)

    design_char  = safe_char(suffix, 0)
    control_type = safe_char(suffix, 1)
    controller   = safe_char(suffix, 2)
    orientation  = safe_char(suffix, 3)
    failsafe     = safe_char(suffix, 4)

    _CSCP_PROTOCOL_CONTROLLERS = {"B", "D", "P"}
    _CSCP_KNOWN_PROTOCOLS = {"BMT", "500", "501", "504", "505"}
    if product_line == "CSCP" and controller in _CSCP_PROTOCOL_CONTROLLERS:
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
        schema="valve",
    )

    warnings: list[dict] = []
    if product_line == "UNKNOWN":
        warnings.append({
            "logical_field": "family",
            "message": "Unknown product prefix. Decoding attempted with partial parsing.",
        })
    warnings.extend({"logical_field": "base",   "message": w} for w in base_warnings)
    warnings.extend({"logical_field": "suffix", "message": w} for w in suffix_warnings)

    return True, warnings, parsed_model


# ── Non-valve schema parsers (PBC, FHD500, FHD130, ZPS, Upgrade Kits) ────────

def _make_nonvalve_parsed(normalized: str, product_line: str, schema: str, **fields) -> ParsedModel:
    """Construct a ParsedModel for a non-valve schema. Most valve fields stay
    blank; the schema-specific ones come in via kwargs."""
    return ParsedModel(
        full_model=normalized,
        product_line=product_line,
        base="",
        suffix="",
        prefix=normalized.split("-")[0][:3] if normalized else "",
        construction="",
        qty_char="",
        size_code="",
        pressure="",
        design_char="",
        control_type="",
        controller="",
        orientation="",
        failsafe="",
        schema=schema,
        **fields,
    )


def _parse_pbc_schema(normalized: str, product_line: str) -> tuple[bool, list[dict], "ParsedModel | None"]:
    """PBC: ``PBC[series]-[function]`` (e.g. ``PBC500-ZBH``)."""
    parts = normalized.split("-")
    head = parts[0].replace(" ", "")  # e.g. "PBC500"
    function = parts[1].strip().upper() if len(parts) > 1 else ""

    series = head[3:] if head.startswith("PBC") else ""
    parsed = _make_nonvalve_parsed(
        normalized, product_line, "pbc",
        series=series, function=function,
    )
    return True, [], parsed


def _parse_fhd500_schema(normalized: str, product_line: str) -> tuple[bool, list[dict], "ParsedModel | None"]:
    """FHD500: ``FHD500-[option]-[option]…``."""
    parts = normalized.split("-")
    head = parts[0].replace(" ", "")
    series = head[3:] if head.startswith("FHD") else ""
    options = parse_dash_options(parts[1:]) if len(parts) > 1 else []
    parsed = _make_nonvalve_parsed(
        normalized, product_line, "fhd500",
        series=series, options=options,
    )
    return True, [], parsed


def _parse_fhd130_schema(normalized: str, product_line: str) -> tuple[bool, list[dict], "ParsedModel | None"]:
    """Sentry FHD: ``FHD[series]-[lang]-[option]-[option]…`` (e.g. ``FHD130-ENG-RD1``)."""
    parts = normalized.split("-")
    head = parts[0].replace(" ", "")
    series = head[3:] if head.startswith("FHD") else ""
    language = parts[1].strip().upper() if len(parts) > 1 else ""
    options = parse_dash_options(parts[2:]) if len(parts) > 2 else []
    parsed = _make_nonvalve_parsed(
        normalized, product_line, "fhd130",
        series=series, language=language, options=options,
    )
    return True, [], parsed


def _parse_zps_schema(normalized: str, product_line: str) -> tuple[bool, list[dict], "ParsedModel | None"]:
    """ZPS: ``ZPS[series][module-count]`` — no dashes (e.g. ``ZPS310``)."""
    head = normalized.replace("-", "").replace(" ", "")
    series = head[3:4] if len(head) >= 4 else ""
    module_count = head[4:6] if len(head) >= 6 else ""
    parsed = _make_nonvalve_parsed(
        normalized, product_line, "zps",
        series=series, module_count=module_count,
    )
    return True, [], parsed


def _parse_upgrade_kit_schema(normalized: str, product_line: str) -> tuple[bool, list[dict], "ParsedModel | None"]:
    """Upgrade Kits: same shape as valves but with placeholders + extra
    Existing Valve Type segment. Format:
    ``[family]X[bodies][size][pressure]-X[control][controller]X[failsafe]-[existing-type]-[options]``.
    """
    parts = normalized.split("-")
    raw_base = parts[0] if parts else ""
    raw_suffix = parts[1] if len(parts) > 1 else ""

    base, base_warnings = normalize_base(raw_base, expected_len=8)
    suffix, suffix_warnings = normalize_suffix(raw_suffix, expected_len=5)

    prefix = base[0:3]
    construction = safe_char(base, 3)  # 'X' placeholder
    qty_char = safe_char(base, 4)
    size_code = base[5:7] if len(base) >= 7 else "??"
    pressure = safe_char(base, 7)

    design_char  = safe_char(suffix, 0)  # 'X' placeholder
    control_type = safe_char(suffix, 1)
    controller   = safe_char(suffix, 2)
    orientation  = safe_char(suffix, 3)  # 'X' placeholder
    failsafe     = safe_char(suffix, 4)

    existing_type = parts[2].strip().upper() if len(parts) > 2 else ""
    options = parse_dash_options(parts[3:]) if len(parts) > 3 else []

    parsed = ParsedModel(
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
        protocol="",
        options=options,
        schema="upgrade_kit",
        existing_type=existing_type,
    )

    warnings: list[dict] = []
    warnings.extend({"logical_field": "base",   "message": w} for w in base_warnings)
    warnings.extend({"logical_field": "suffix", "message": w} for w in suffix_warnings)
    return True, warnings, parsed


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


def _decode_single_code(code: str, mapping: dict) -> str:
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
        config["construction_label"]: _decode_single_code(parsed_model.construction, config["construction_map"]),
        config["bodies_label"]: _decode_single_code(parsed_model.qty_char, config["bodies_map"]),
        config["size_label"]: _decode_single_code(parsed_model.size_code, config["size_map"]),
        config["pressure_label"]: _decode_single_code(parsed_model.pressure, config["pressure_map"]),
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
    schema = parsed_model.schema
    if schema == "pbc":
        return _decode_pbc(parsed_model, config)
    if schema == "fhd500":
        return _decode_fhd500(parsed_model, config)
    if schema == "fhd130":
        return _decode_fhd130(parsed_model, config)
    if schema == "zps":
        return _decode_zps(parsed_model, config)
    if schema == "upgrade_kit":
        return _decode_upgrade_kit(parsed_model, config)
    return _decode_with_config_labels(parsed_model, config)


def _decode_pbc(parsed_model: ParsedModel, config: dict) -> dict[str, str]:
    return {
        "Product Line": PRODUCT_DISPLAY_NAMES.get(parsed_model.product_line, parsed_model.product_line),
        config["family_label"]: f"PBC -> {config['family_map'].get('PBC', 'Programmable BACnet Controller')}",
        config["series_label"]: _decode_single_code(parsed_model.series, config["series_map"]),
        config["function_label"]: _decode_single_code(parsed_model.function, config["function_map"]),
    }


def _decode_fhd500(parsed_model: ParsedModel, config: dict) -> dict[str, str]:
    return {
        "Product Line": PRODUCT_DISPLAY_NAMES.get(parsed_model.product_line, parsed_model.product_line),
        config["family_label"]: f"FHD -> {config['family_map'].get('FHD', 'Fume Hood Display')}",
        config["series_label"]: _decode_single_code(parsed_model.series, config["series_map"]),
        config["options_label"]: decode_option_list(parsed_model.options, config["option_map"]),
    }


def _decode_fhd130(parsed_model: ParsedModel, config: dict) -> dict[str, str]:
    return {
        "Product Line": PRODUCT_DISPLAY_NAMES.get(parsed_model.product_line, parsed_model.product_line),
        config["family_label"]: f"FHD -> {config['family_map'].get('FHD', 'Fume Hood Display')}",
        config["series_label"]: _decode_single_code(parsed_model.series, config["series_map"]),
        config["language_label"]: _decode_single_code(parsed_model.language, config["language_map"]),
        config["options_label"]: decode_option_list(parsed_model.options, config["option_map"]),
    }


def _decode_zps(parsed_model: ParsedModel, config: dict) -> dict[str, str]:
    return {
        "Product Line": PRODUCT_DISPLAY_NAMES.get(parsed_model.product_line, parsed_model.product_line),
        config["family_label"]: f"ZPS -> {config['family_map'].get('ZPS', 'Zone Presence Sensor')}",
        config["series_label"]: _decode_single_code(parsed_model.series, config["series_map"]),
        config["module_count_label"]: _decode_single_code(parsed_model.module_count, config["module_count_map"]),
    }


def _decode_upgrade_kit(parsed_model: ParsedModel, config: dict) -> dict[str, str]:
    return {
        "Product Line": PRODUCT_DISPLAY_NAMES.get(parsed_model.product_line, parsed_model.product_line),
        config["family_label"]: (
            f"{parsed_model.prefix} -> {config['family_map'].get(parsed_model.prefix, 'Not a valid entry')}"
        ),
        config["bodies_label"]: _decode_single_code(parsed_model.qty_char, config["bodies_map"]),
        config["size_label"]: _decode_single_code(parsed_model.size_code, config["size_map"]),
        config["pressure_label"]: _decode_single_code(parsed_model.pressure, config["pressure_map"]),
        config["control_label"]: _decode_single_code(parsed_model.control_type, config["control_map"]),
        config["controller_label"]: _decode_single_code(parsed_model.controller, config["controller_map"]),
        config["failsafe_label"]: _decode_single_code(parsed_model.failsafe, config["failsafe_map"]),
        config["existing_type_label"]: _decode_single_code(parsed_model.existing_type, config["existing_type_map"]),
        "Options": decode_option_list(parsed_model.options, config["option_map"]),
    }


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
    """Validation rules for Celeris II per PDS p.12 (MKT-0006 Rev F).

    Notes 1-5 from the PDS map to specific rules below; comments cite each note.
    """
    labels = validation_field_labels(parsed_model.product_line)

    # Note 1: Construction D — single body only, sizes 08/10/12, no SFB/SFX.
    if parsed_model.construction == "D":
        require_in(validation_issues, labels["bodies"], parsed_model.qty_char, {"F", "1"},
                   "Celeris II Construction D is limited to Bodies = F or 1.")
        require_in(validation_issues, labels["size"], parsed_model.size_code, {"08", "10", "12"},
                   "Celeris II Construction D is limited to Sizes 08, 10, and 12.")
        if any(opt in parsed_model.options for opt in ("SFB", "SFX")):
            add_validation_issue(validation_issues, labels["options"],
                                 "Celeris II Construction D cannot be ordered with SFB or SFX.")

    # Bodies = 2 → only sizes 10/12/14 (per bodies_map description).
    if parsed_model.qty_char == "2" and parsed_model.size_code not in ("10", "12", "14"):
        add_validation_issue(validation_issues, labels["bodies"],
                             "Celeris II dual valves (Bodies = 2) are only available for sizes 10, 12, and 14.")

    # Control Type H is limited to single 8/10/12-inch valves.
    if parsed_model.control_type == "H":
        require_in(validation_issues, labels["bodies"], parsed_model.qty_char, {"F", "1"},
                   "Celeris II Control Type H is limited to single-body valves (Bodies = F or 1).")
        require_in(validation_issues, labels["size"], parsed_model.size_code, {"08", "10", "12"},
                   "Celeris II Control Type H is limited to Sizes 08, 10, and 12.")

    # Controller H = Hood exhaust valve — must be on EXV (exhaust prefix).
    if parsed_model.controller == "H" and parsed_model.prefix != "EXV":
        add_validation_issue(validation_issues, labels["controller"],
                             "Celeris II Controller H (Hood exhaust) is only valid on EXV exhaust valves.")

    # Note 2: Hood valves cannot have low-speed actuators (Control Type = H, I, or L).
    if parsed_model.controller == "H" and parsed_model.control_type in {"H", "I", "L"}:
        add_validation_issue(validation_issues, labels["control"],
                             "Celeris II Hood valves (Controller H) cannot use low-speed actuators (Control = H, I, or L).")

    # Note 4: Option REO — pneumatic actuators only (Control = N), Horizontal only.
    if "REO" in parsed_model.options:
        if parsed_model.control_type != "N":
            add_validation_issue(validation_issues, labels["options"],
                                 "Celeris II Option REO is limited to pneumatic actuators (Control Type = N).")
        if parsed_model.orientation != "H":
            add_validation_issue(validation_issues, labels["options"],
                                 "Celeris II Option REO requires Horizontal orientation.")

    # Note 5: Option WRE — IP-rated electric actuators (Control = I, L, or M), Horizontal only.
    if "WRE" in parsed_model.options:
        if parsed_model.control_type not in ("I", "L", "M"):
            add_validation_issue(validation_issues, labels["options"],
                                 "Celeris II Option WRE requires an IP-rated electric actuator "
                                 "(Control Type = I, L, or M).")
        if parsed_model.orientation != "H":
            add_validation_issue(validation_issues, labels["options"],
                                 "Celeris II Option WRE requires Horizontal orientation.")

    # Option SSB requires Construction A (or Body Design A — but Celeris II is
    # Design A only, so that branch is automatically satisfied). Practically:
    # SSB → Construction A.
    if "SSB" in parsed_model.options and parsed_model.construction != "A":
        add_validation_issue(validation_issues, labels["options"],
                             "Celeris II Option SSB is limited to Construction A (or Body Design A).")


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
        # Stainless variants (E/F) don't accept square flange or stainless-shaft options
        # — those options don't apply to a stainless body. Confirmed against the
        # CSCP Stainless ordering page (the "image 1" screenshot).
        stainless_blocked_opts = [o for o in parsed_model.options if o in ("SFB", "SFD", "SFI", "SSB")]
        if stainless_blocked_opts:
            add_validation_issue(validation_issues, labels["options"],
                                 f"CSCP Stainless (Construction {parsed_model.construction}) cannot be ordered with "
                                 f"option(s) {', '.join(stainless_blocked_opts)} — square flange and stainless-bracket "
                                 "options don't apply to stainless valve bodies.")

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


# LonMark valve controllers for Theris (MKT-0118) and Traccel (MKT-0041).
# WRE option is only valid on these controllers — it's not offered on the
# BACnet variants (A, B, C, D, P, Y, Z, N).
_THERIS_LONMARK_CONTROLLERS = {"E", "O", "X"}
_TRACCEL_LONMARK_CONTROLLERS = {"E", "O", "X"}


def _validate_theris_traccel_structural(parsed_model: ParsedModel, validation_issues: list[dict], product_label: str) -> None:
    """Shared structural constraints — apply identically to Theris and Traccel
    per their ordering-guide notes (MKT-0228/MKT-0118 and MKT-0242/MKT-0041)."""
    labels = validation_field_labels(parsed_model.product_line)

    # Note 1: 8" S/L shut-off → Construction A only.
    if parsed_model.size_code == "08" and parsed_model.design_char in ("S", "L") and parsed_model.construction != "A":
        add_validation_issue(validation_issues, labels["construction"],
                             f"{product_label} 8-inch shut-off valves (Design = S or L) require Construction = A.")

    # Note 2: 14" + Pressure M + Design L → unavailable.
    if parsed_model.size_code == "14" and parsed_model.pressure == "M" and parsed_model.design_char == "L":
        add_validation_issue(validation_issues, labels["design"],
                             f"{product_label} 14-inch valves are not available as Low Leakage Shut-off (Design = L) "
                             "with Medium Pressure (Range = M).")

    # Note 4: Pressure L + Design L → unavailable.
    if parsed_model.pressure == "L" and parsed_model.design_char == "L":
        add_validation_issue(validation_issues, labels["design"],
                             f"{product_label} Low Pressure (Range = L), Low Leakage Shut-off (Design = L) "
                             "valves are not available in any size.")

    # Note 3: Pressure L + Design S + Orientation U → unavailable.
    if parsed_model.pressure == "L" and parsed_model.design_char == "S" and parsed_model.orientation == "U":
        add_validation_issue(validation_issues, labels["orientation"],
                             f"{product_label} Low Pressure (Range = L), Standard Shut-off (Design = S) "
                             "valves are not available in vertical upflow (Orientation = U).")

    # Bodies = 2 is documented as "available for 10\", 12\", and 14\" only" on
    # all four ordering guides — explicit constraint not covered by bodies_map.
    if parsed_model.qty_char == "2" and parsed_model.size_code not in ("10", "12", "14"):
        add_validation_issue(validation_issues, labels["bodies"],
                             f"{product_label} dual valves (Bodies = 2) are only available for sizes 10, 12, and 14.")


def _validate_wre_constraints(parsed_model: ParsedModel, validation_issues: list[dict],
                              product_label: str, lonmark_controllers: set[str]) -> None:
    """WRE option constraints from MKT-0118 / MKT-0041 Note 6 + Note 7:
       - Controller must be LonMark (E, O, X)
       - Orientation must be Horizontal (H)
       - Control Type must be I or L (NEMA-1 H actuators don't have an IP rating)."""
    if "WRE" not in parsed_model.options:
        return
    labels = validation_field_labels(parsed_model.product_line)

    if parsed_model.controller not in lonmark_controllers:
        add_validation_issue(validation_issues, labels["options"],
                             f"{product_label} Option WRE is only available on LonMark valves "
                             "(Controller = E, O, or X).")
    if parsed_model.orientation != "H":
        add_validation_issue(validation_issues, labels["options"],
                             f"{product_label} Option WRE requires Horizontal orientation (Orientation = H).")
    if parsed_model.control_type not in ("I", "L"):
        add_validation_issue(validation_issues, labels["options"],
                             f"{product_label} Option WRE requires an IP-rated actuator "
                             "(Control Type = I or L); not available with the NEMA-1 Control Type H.")


def validate_theris_rules(parsed_model: ParsedModel, validation_issues: list[dict]) -> None:
    _validate_theris_traccel_structural(parsed_model, validation_issues, "Theris")
    _validate_wre_constraints(parsed_model, validation_issues, "Theris", _THERIS_LONMARK_CONTROLLERS)


def validate_venturian_rules(parsed_model: ParsedModel, validation_issues: list[dict]) -> None:
    """Venturian validation rules per PDS p.31 (MKT-0006 Rev F).

    Notes 1-18 from the PDS map to discrete rules below; comments cite each.
    """
    labels = validation_field_labels(parsed_model.product_line)
    family = parsed_model.prefix

    # Bodies = 2 → only sizes 10/12/14 (Notes 9, 13).
    if parsed_model.qty_char == "2" and parsed_model.size_code not in ("10", "12", "14"):
        add_validation_issue(validation_issues, labels["bodies"],
                             "Venturian dual valves (Bodies = 2) only available for sizes 10, 12, and 14 (Notes 9, 13).")

    # Size 08 → single body only.
    if parsed_model.size_code == "08" and parsed_model.qty_char == "2":
        add_validation_issue(validation_issues, labels["bodies"],
                             "Venturian Size 08 is single-body only.")

    # Note 4: Vertical Down orientation → single only.
    if parsed_model.orientation == "D" and parsed_model.qty_char == "2":
        add_validation_issue(validation_issues, labels["orientation"],
                             "Venturian Vertical Down orientation is single-body only (Note 4).")

    # Note 6: Pressure L + Design S → not available in Vertical Up.
    if parsed_model.pressure == "L" and parsed_model.design_char == "S" and parsed_model.orientation == "U":
        add_validation_issue(validation_issues, labels["orientation"],
                             "Venturian Low Pressure + Standard Shut-off not available in Vertical Up (Note 6).")

    # Note 7: Constant Volume (Control C) → Design A mandatory.
    if parsed_model.control_type == "C" and parsed_model.design_char != "A":
        add_validation_issue(validation_issues, labels["design"],
                             "Venturian Constant Volume (Control C) requires Design = A (Note 7).")

    # Note 10: Control H → 8/10/12-inch single VAV only.
    if parsed_model.control_type == "H":
        if parsed_model.size_code not in ("08", "10", "12"):
            add_validation_issue(validation_issues, labels["size"],
                                 "Venturian Control H is limited to 8/10/12-inch valves (Note 10).")
        if parsed_model.qty_char != "1":
            add_validation_issue(validation_issues, labels["bodies"],
                                 "Venturian Control H is single-body only (Note 10).")

    # Note 9: Control L mandatory on single 14-inch and dual VAV valves.
    if parsed_model.size_code == "14" and parsed_model.qty_char == "1" and parsed_model.control_type != "L":
        add_validation_issue(validation_issues, labels["control"],
                             "Venturian 14-inch single VAV requires Control = L (Note 9).")
    if parsed_model.qty_char == "2" and parsed_model.control_type != "L":
        add_validation_issue(validation_issues, labels["control"],
                             "Venturian dual valves require Control = L (Note 9).")

    # Note 14: Constant Volume valves require Designation N.
    if parsed_model.control_type == "C" and parsed_model.controller != "N":
        add_validation_issue(validation_issues, labels["controller"],
                             "Venturian Constant Volume valves require Controller = N (Note 14).")

    # Note 11: Option EVI → exhaust valves (VEV) only.
    if "EVI" in parsed_model.options and family != "VEV":
        add_validation_issue(validation_issues, labels["options"],
                             "Venturian Option EVI is only available on exhaust valves (VEV) (Note 11).")

    # Note 13: Options SFB/SFD/SFI cannot be ordered with Bodies F or 2.
    if any(o in parsed_model.options for o in ("SFB", "SFD", "SFI")) and parsed_model.qty_char in ("F", "2"):
        add_validation_issue(validation_issues, labels["options"],
                             "Venturian Options SFB/SFD/SFI cannot be ordered with Bodies F or 2 (Note 13).")

    # Note 17: Designations B & D only on non-shut-off valves (Design A).
    if parsed_model.controller in ("B", "D") and parsed_model.design_char != "A":
        add_validation_issue(validation_issues, labels["controller"],
                             "Venturian Designations B and D only available on non-shut-off valves (Design A) (Note 17).")

    # Note 18: Designation D → supply valves (VSV) only.
    if parsed_model.controller == "D" and family != "VSV":
        add_validation_issue(validation_issues, labels["controller"],
                             "Venturian Designation D (TP) is only available on supply valves (VSV) (Note 18).")


def validate_theris_flex_rules(parsed_model: ParsedModel, validation_issues: list[dict]) -> None:
    """Theris FLEX validation rules per PDS p.24 (MKT-0006 Rev F).

    Notes 1-11 from the PDS map to discrete rules below; comments cite each.
    """
    labels = validation_field_labels(parsed_model.product_line)
    family = parsed_model.prefix

    # Note 1: FEV (Flex exhaust) limited to Controllers C, D, N, V.
    if family == "FEV" and parsed_model.controller not in ("C", "D", "N", "V"):
        add_validation_issue(validation_issues, labels["controller"],
                             "Theris FLEX exhaust (FEV) requires Controller in {C, D, N, V} (Note 1).")

    # Note 2: FSV (Flex supply) limited to Controllers A, C, D, V.
    if family == "FSV" and parsed_model.controller not in ("A", "C", "D", "V"):
        add_validation_issue(validation_issues, labels["controller"],
                             "Theris FLEX supply (FSV) requires Controller in {A, C, D, V} (Note 2).")

    # Note 4: Size 06 NOT available with Range = L or Orientation = D.
    if parsed_model.size_code == "06":
        if parsed_model.pressure == "L":
            add_validation_issue(validation_issues, labels["pressure"],
                                 "Theris FLEX Size 06 is not available with Low pressure (Note 4).")
        if parsed_model.orientation == "D":
            add_validation_issue(validation_issues, labels["orientation"],
                                 "Theris FLEX Size 06 is not available with Vertical Down orientation (Note 4).")

    # Note 7: Option EVI limited to exhaust valves (FEV).
    if "EVI" in parsed_model.options and family != "FEV":
        add_validation_issue(validation_issues, labels["options"],
                             "Theris FLEX Option EVI is only available on exhaust valves (FEV) (Note 7).")

    # Note 7/8: EVI and IBO are mutually exclusive.
    if "EVI" in parsed_model.options and "IBO" in parsed_model.options:
        add_validation_issue(validation_issues, labels["options"],
                             "Theris FLEX Options EVI and IBO are mutually exclusive (Notes 7, 8).")

    # Note 11: SFB, SFD, SFI cannot be ordered with each other.
    square_opts = [o for o in parsed_model.options if o in ("SFB", "SFD", "SFI")]
    if len(square_opts) > 1:
        add_validation_issue(validation_issues, labels["options"],
                             "Theris FLEX Options SFB/SFD/SFI cannot be ordered with each other (Note 11).")


def validate_traccel_rules(parsed_model: ParsedModel, validation_issues: list[dict]) -> None:
    _validate_theris_traccel_structural(parsed_model, validation_issues, "Traccel")
    _validate_wre_constraints(parsed_model, validation_issues, "Traccel", _TRACCEL_LONMARK_CONTROLLERS)

    # Traccel-specific (MKT-0041 omits Control Type H from the LonMark
    # ordering guide; H is BACnet-only on Traccel). Theris LonMark DOES
    # list Control H, so this rule does not apply to Theris.
    labels = validation_field_labels(parsed_model.product_line)
    if parsed_model.control_type == "H" and parsed_model.controller in _TRACCEL_LONMARK_CONTROLLERS:
        add_validation_issue(validation_issues, labels["control"],
                             "Traccel Control Type H (NEMA-1 rotary) is only offered with BACnet controllers; "
                             "not available with LonMark controllers (E, O, or X).")


def validate_base_upgradeable_tiered_rules(parsed_model: ParsedModel, validation_issues: list[dict]) -> None:
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


def validate_base_upgradeable_cv_rules(parsed_model: ParsedModel, validation_issues: list[dict]) -> None:
    """Validation rules for Constant Volume / Base Upgradeable per PDS p.34
    (MKT-0006 Rev F). Notes 1-13 from the PDS map to the rules below."""
    labels = validation_field_labels(parsed_model.product_line)
    family = parsed_model.prefix
    is_cv = family in ("CSV", "CEV")
    is_bxv = family in ("BSV", "BEV")

    # Note 1: CSV/CEV are Constant Volume — Design A only, Control C only.
    if is_cv:
        if parsed_model.design_char != "A":
            add_validation_issue(validation_issues, labels["design"],
                                 f"{family}: Constant Volume valves are available in Design A only (Note 1).")
        if parsed_model.control_type != "C":
            add_validation_issue(validation_issues, labels["control"],
                                 f"{family}: Constant Volume valves require Control = C.")

    # BxV cannot use Control Type C (that's CV-only).
    if is_bxv and parsed_model.control_type == "C":
        add_validation_issue(validation_issues, labels["control"],
                             f"{family}: Control Type C is reserved for Constant Volume (CSV/CEV) valves.")

    # Note 2: Construction D — single body only, Design A only, no SFB/SFD/SFI.
    if parsed_model.construction == "D":
        require_in(validation_issues, labels["bodies"], parsed_model.qty_char, {"F", "1"},
                   "Construction D is limited to Bodies = F or 1 (Note 2).")
        if parsed_model.design_char != "A":
            add_validation_issue(validation_issues, labels["design"],
                                 "Construction D requires Design = A (Note 2).")
        if any(opt in parsed_model.options for opt in ("SFB", "SFD", "SFI")):
            add_validation_issue(validation_issues, labels["options"],
                                 "Construction D cannot be ordered with SFB, SFD, or SFI (Note 2).")

    # Note 3: 8-inch shut-off (Design L or S) requires Construction A.
    if parsed_model.size_code == "08" and parsed_model.design_char in ("L", "S") and parsed_model.construction != "A":
        add_validation_issue(validation_issues, labels["construction"],
                             "8-inch shut-off valves (Design L or S) require Construction A (Note 3).")

    # Note 4: 14-inch + Pressure M + Design L → not available.
    if parsed_model.size_code == "14" and parsed_model.pressure == "M" and parsed_model.design_char == "L":
        add_validation_issue(validation_issues, labels["design"],
                             "14-inch medium pressure low leakage valves are not available (Note 4).")

    # Note 5: 14-inch + Control B or F → singles only; Control B further → Controller N only.
    if parsed_model.size_code == "14" and parsed_model.control_type in ("B", "F"):
        if parsed_model.qty_char not in ("F", "1"):
            add_validation_issue(validation_issues, labels["bodies"],
                                 "14-inch pneumatic/fixed (Control B/F) valves are single-body only (Note 5).")
        if parsed_model.control_type == "B" and parsed_model.controller != "N":
            add_validation_issue(validation_issues, labels["controller"],
                                 "14-inch pneumatic (Control B) requires Controller = N (Note 5).")

    # Note 6: Low pressure + Low leakage → not available any size.
    if parsed_model.pressure == "L" and parsed_model.design_char == "L":
        add_validation_issue(validation_issues, labels["design"],
                             "Low pressure low leakage shut-off valves are not available in any size (Note 6).")

    # Note 7: Low pressure + Standard shut-off → not available in vertical up.
    if parsed_model.pressure == "L" and parsed_model.design_char == "S" and parsed_model.orientation == "U":
        add_validation_issue(validation_issues, labels["orientation"],
                             "Low pressure standard shut-off valves are not available in vertical up (Note 7).")

    # Note 8: Control H or L REQUIRE flow feedback (Controller F).
    if parsed_model.control_type in ("H", "L") and parsed_model.controller != "F":
        add_validation_issue(validation_issues, labels["controller"],
                             "Control Types H and L require flow feedback (Controller = F) (Note 8).")

    # Note 9: Control I or Z on shut-off valves (Design L or S) require Controller F.
    if parsed_model.control_type in ("I", "Z") and parsed_model.design_char in ("L", "S") and parsed_model.controller != "F":
        add_validation_issue(validation_issues, labels["controller"],
                             "Control I or Z on shut-off valves require flow feedback (Controller = F) (Note 9).")

    # Failsafe rules — C/O for Control B only; Z not for Control B.
    if parsed_model.failsafe in ("C", "O") and parsed_model.control_type != "B":
        add_validation_issue(validation_issues, labels["failsafe"],
                             "Fail-Safe C or O is only valid with Control Type B (pneumatic).")
    if parsed_model.failsafe == "Z" and parsed_model.control_type == "B":
        add_validation_issue(validation_issues, labels["failsafe"],
                             "Fail-Safe Z is not valid for Control Type B (pneumatic uses C or O).")

    # Note 11: Option REO — pneumatic actuators only (Control B + Controller F), Horizontal only.
    if "REO" in parsed_model.options:
        if parsed_model.control_type != "B":
            add_validation_issue(validation_issues, labels["options"],
                                 "Option REO requires pneumatic actuator (Control = B) (Note 11).")
        if parsed_model.controller != "F":
            add_validation_issue(validation_issues, labels["options"],
                                 "Option REO requires flow feedback (Controller = F) (Note 11).")
        if parsed_model.orientation != "H":
            add_validation_issue(validation_issues, labels["options"],
                                 "Option REO requires Horizontal orientation (Note 11).")

    # Note 10: Option REI requires Controller = F.
    if "REI" in parsed_model.options and parsed_model.controller != "F":
        add_validation_issue(validation_issues, labels["options"],
                             "Option REI requires flow feedback (Controller = F) (Note 10).")

    # Note 12: SFB/SFD/SFI — not with Construction D, Bodies F/2/3/4, nor each other.
    square_opts = [o for o in parsed_model.options if o in ("SFB", "SFD", "SFI")]
    if len(square_opts) > 1:
        add_validation_issue(validation_issues, labels["options"],
                             "Options SFB, SFD, and SFI cannot be ordered with each other (Note 12).")
    if square_opts and parsed_model.qty_char in ("F", "2", "3", "4"):
        add_validation_issue(validation_issues, labels["options"],
                             "Options SFB/SFD/SFI require Bodies = 1 (Note 12).")

    # Note 13: VPO/VPT — Control Type B or F only; not with REI or REO.
    vpx_opts = [o for o in parsed_model.options if o in ("VPO", "VPT")]
    if vpx_opts:
        if parsed_model.control_type not in ("B", "F"):
            add_validation_issue(validation_issues, labels["options"],
                                 "Options VPO/VPT are limited to Control Type B or F (Note 13).")
        if any(opt in parsed_model.options for opt in ("REI", "REO")):
            add_validation_issue(validation_issues, labels["options"],
                                 "Options VPO/VPT cannot be combined with REI or REO (Note 13).")


# ── Notes for Constant Volume / Base Upgradeable (PDS p.34) ───────────────────
notes_base_upgradeable_cv = {
    "1": "Note 1: CSV and CEV (Constant Volume) valves are available in Design A only.",
    "2": "Note 2: Construction D is ONLY available in single-body valves (Bodies = F or 1) of Design A without square flanges (Options SFB, SFD, or SFI).",
    "3": "Note 3: 8-inch shut-off valves (Design L or S) are ONLY available in Construction A (uncoated).",
    "4": "Note 4: 14-inch medium pressure (Range = M) low leakage shutoff valves (Design = L) are NOT available.",
    "5": "Note 5: 14-inch pneumatic and fixed (Control = B or F) are only available in single bodies; Control B is further limited to Controller = N only.",
    "6": "Note 6: Low pressure (Range = L), low leakage shut-off (Design = L) valves are NOT available in any size.",
    "7": "Note 7: Low pressure (Range = L), standard shut-off (Design = S) valves are NOT available in vertical up (Orientation = U).",
    "8": "Note 8: Control Types H and L REQUIRE flow feedback (Controller = F). Cannot be mechanically clamped.",
    "9": "Note 9: Control Types I and Z on shut-off valves (Design L and S) REQUIRE flow feedback (Controller = F). Can be mechanically clamped.",
    "10": "Note 10: Option REI: Remote Electronics Indoor installations only. 75 ft (22.8 m) of pneumatic tubing for pneumatic actuators (Control = B + Controller = F). 150 ft (45.7 m) of 22 gauge cable for low-speed electric actuators (Control = H, I, L, or Z + Controller = F).",
    "11": "Note 11: Option REO: Remote Electronics Outdoor installations only. Limited to pneumatically actuated valves (Control = B + Controller = F). Horizontal orientation only.",
    "12": "Note 12: Options SFB, SFD, or SFI cannot be ordered with Construction D, Bodies F/2/3/4, nor with each other.",
    "13": "Note 13: Options VPO and VPT are limited to Control = B or F ONLY. NOT available with Options REI or REO.",
}


def build_base_upgradeable_cv_notes(parsed_model: ParsedModel, include_table_text: bool = True) -> list[str]:
    note_lines: list[str] = []
    if parsed_model.prefix == "BSV":
        note_lines.append("Note: Supply valves come standard with insulation and blocks.")
    if parsed_model.prefix in ("CSV", "CEV"):
        note_lines.append(notes_base_upgradeable_cv["1"])
    if parsed_model.construction == "D":
        note_lines.append(notes_base_upgradeable_cv["2"])
    if parsed_model.size_code == "08" and parsed_model.design_char in ("L", "S"):
        note_lines.append(notes_base_upgradeable_cv["3"])
    if parsed_model.size_code == "14" and parsed_model.pressure == "M" and parsed_model.design_char == "L":
        note_lines.append(notes_base_upgradeable_cv["4"])
    if parsed_model.size_code == "14" and parsed_model.control_type in ("B", "F"):
        note_lines.append(notes_base_upgradeable_cv["5"])
    if "PSL" in parsed_model.options:
        note_lines.append("Note: Pressure switch alarm setpoint is 0.3\" WC for medium pressure / 0.2\" WC for low pressure.")
    if parsed_model.pressure == "L" and parsed_model.design_char == "L":
        note_lines.append(notes_base_upgradeable_cv["6"])
    if parsed_model.pressure == "L" and parsed_model.design_char == "S":
        note_lines.append(notes_base_upgradeable_cv["7"])
    if parsed_model.control_type in ("H", "L"):
        note_lines.append(notes_base_upgradeable_cv["8"])
    if parsed_model.control_type in ("I", "Z") and parsed_model.design_char in ("L", "S"):
        note_lines.append(notes_base_upgradeable_cv["9"])
    if "REI" in parsed_model.options:
        note_lines.append(notes_base_upgradeable_cv["10"])
    if "REO" in parsed_model.options:
        note_lines.append(notes_base_upgradeable_cv["11"])
    if any(o in parsed_model.options for o in ("SFB", "SFD", "SFI")):
        note_lines.append(notes_base_upgradeable_cv["12"])
    if any(o in parsed_model.options for o in ("VPO", "VPT")):
        note_lines.append(notes_base_upgradeable_cv["13"])
    _append_product_table_note(note_lines, parsed_model, include_table_text)
    return note_lines


def _apply_structural_warnings(parsed_model: ParsedModel, warnings: list[dict], validation_issues: list[dict]) -> None:
    """Route structured warnings from parse_model to validation_issues using
    the product-specific display label for each logical field."""
    if not warnings:
        return
    labels = validation_field_labels(parsed_model.product_line)
    for warning in warnings:
        field = labels.get(warning["logical_field"], warning["logical_field"])
        add_validation_issue(validation_issues, field, warning["message"])


def _summarize_warnings(warnings: list[dict]) -> str:
    """Backwards-compatible single-line summary of structural warnings."""
    if not warnings:
        return "Valid"
    return " | ".join(w["message"] for w in warnings)


def validate_model(parsed_model: ParsedModel) -> list[dict]:
    if parsed_model.product_line == "UNKNOWN":
        return validate_unknown_model(parsed_model)

    validation_issues: list[dict] = []

    # Non-valve schemas have their own validators; the valve common-code
    # check doesn't apply to them.
    if parsed_model.schema == "pbc":
        validate_pbc_rules(parsed_model, validation_issues)
        return dedupe_validation_issues(validation_issues)
    if parsed_model.schema == "fhd500":
        validate_fhd500_rules(parsed_model, validation_issues)
        return dedupe_validation_issues(validation_issues)
    if parsed_model.schema == "fhd130":
        validate_fhd130_rules(parsed_model, validation_issues)
        return dedupe_validation_issues(validation_issues)
    if parsed_model.schema == "zps":
        validate_zps_rules(parsed_model, validation_issues)
        return dedupe_validation_issues(validation_issues)
    if parsed_model.schema == "upgrade_kit":
        validate_upgrade_kit_rules(parsed_model, validation_issues)
        return dedupe_validation_issues(validation_issues)

    validate_common_codes(
        parsed_model,
        validation_issues,
        analog_numeric_special_options=(parsed_model.product_line == "ANALOG"),
    )

    if parsed_model.product_line == "CELERIS_II":
        validate_celeris_rules(parsed_model, validation_issues)
    elif parsed_model.product_line == "CSCP":
        validate_cscp_rules(parsed_model, validation_issues)
    elif parsed_model.product_line == "BASE_UPGRADEABLE_TIERED":
        validate_base_upgradeable_tiered_rules(parsed_model, validation_issues)
    elif parsed_model.product_line == "BASE_UPGRADEABLE_CV":
        validate_base_upgradeable_cv_rules(parsed_model, validation_issues)
    elif parsed_model.product_line == "ANALOG":
        validate_analog_rules(parsed_model, validation_issues)
    elif parsed_model.product_line == "THERIS":
        validate_theris_rules(parsed_model, validation_issues)
    elif parsed_model.product_line == "THERIS_FLEX":
        validate_theris_flex_rules(parsed_model, validation_issues)
    elif parsed_model.product_line == "TRACCEL":
        validate_traccel_rules(parsed_model, validation_issues)
    elif parsed_model.product_line == "VENTURIAN":
        validate_venturian_rules(parsed_model, validation_issues)

    return dedupe_validation_issues(validation_issues)


# ── Non-valve validators (PBC, FHD, ZPS, Upgrade Kits) ────────────────────────

def validate_pbc_rules(parsed_model: ParsedModel, validation_issues: list[dict]) -> None:
    """PBC: PBC[series]-[function] per PDS p.11."""
    if parsed_model.series not in ("500", "501", "504", "505"):
        add_validation_issue(validation_issues, "Series",
                             f"PBC series must be 500, 501, 504, or 505 (got {parsed_model.series or 'empty'}).")
    if parsed_model.function and parsed_model.function not in ("GEN", "ZBH", "ZBL"):
        add_validation_issue(validation_issues, "Function",
                             f"PBC function must be GEN, ZBH, or ZBL (got {parsed_model.function}).")
    if not parsed_model.function:
        add_validation_issue(validation_issues, "Function",
                             "PBC requires a function code (GEN, ZBH, or ZBL).")


def validate_fhd500_rules(parsed_model: ParsedModel, validation_issues: list[dict]) -> None:
    """FHD500: FHD500-[options] per PDS p.56."""
    if parsed_model.series != "500":
        add_validation_issue(validation_issues, "Network/Protocol",
                             f"FHD500 requires series = 500 (got {parsed_model.series or 'empty'}).")
    valid_options = {"DHV", "HV", "HUB", "HUV", "RD1", "RM1", "RM3"}
    for opt in parsed_model.options:
        if opt not in valid_options:
            add_validation_issue(validation_issues, "Options",
                                 f"{opt} is not a valid FHD500 option.")
    # Per user: at most one of {DHV, HUB, HUV} and one of {RD1, RM1, RM3}.
    hub_group = [o for o in parsed_model.options if o in ("DHV", "HUB", "HUV")]
    if len(hub_group) > 1:
        add_validation_issue(validation_issues, "Options",
                             "FHD500 accepts only one of DHV, HUB, or HUV.")
    mount_group = [o for o in parsed_model.options if o in ("RD1", "RM1", "RM3")]
    if len(mount_group) > 1:
        add_validation_issue(validation_issues, "Options",
                             "FHD500 accepts only one of RD1, RM1, or RM3.")


def validate_fhd130_rules(parsed_model: ParsedModel, validation_issues: list[dict]) -> None:
    """Sentry FHD: FHD[series]-[lang]-[options] per PDS p.57."""
    if parsed_model.series != "130":
        add_validation_issue(validation_issues, "Series",
                             f"Sentry FHD requires series = 130 (got {parsed_model.series or 'empty'}).")
    if parsed_model.language not in ("ENG", "FRC"):
        add_validation_issue(validation_issues, "Language",
                             f"Sentry FHD language must be ENG or FRC (got {parsed_model.language or 'empty'}).")
    valid_options = {"DHV", "HUB", "FHV", "RD1", "RM1", "RM3"}
    for opt in parsed_model.options:
        if opt not in valid_options:
            add_validation_issue(validation_issues, "Options",
                                 f"{opt} is not a valid Sentry FHD option.")
    # Note 3: DHV requires HUB.
    if "DHV" in parsed_model.options and "HUB" not in parsed_model.options:
        add_validation_issue(validation_issues, "Options",
                             "Sentry FHD: Option DHV must be ordered with HUB (Note 3).")
    # Note 5: DHV and FHV mutually exclusive.
    if "DHV" in parsed_model.options and "FHV" in parsed_model.options:
        add_validation_issue(validation_issues, "Options",
                             "Sentry FHD: Options DHV and FHV cannot both be ordered (Note 5).")
    # At most one mounting kit.
    mount_group = [o for o in parsed_model.options if o in ("RD1", "RM1", "RM3")]
    if len(mount_group) > 1:
        add_validation_issue(validation_issues, "Options",
                             "Sentry FHD accepts only one mounting-kit option (RD1, RM1, or RM3).")


def validate_zps_rules(parsed_model: ParsedModel, validation_issues: list[dict]) -> None:
    """ZPS: ZPS[series][module-count] per PDS p.58."""
    if parsed_model.series != "3":
        add_validation_issue(validation_issues, "Series",
                             f"ZPS only available in Series 3 (got {parsed_model.series or 'empty'}).")
    if parsed_model.module_count not in ("10", "20", "30", "40"):
        add_validation_issue(validation_issues, "Number of Modules",
                             f"ZPS module count must be 10, 20, 30, or 40 (got {parsed_model.module_count or 'empty'}).")


def validate_upgrade_kit_rules(parsed_model: ParsedModel, validation_issues: list[dict]) -> None:
    """Valve Upgrade Kits per PDS p.54.

    14 enforceable rules + 5 informational notes (5, 7, 8, 18, 22).
    """
    family = parsed_model.prefix
    config = standard_product_configs.get("UPGRADE_KIT", {})
    labels = {k: config.get(f"{k}_label", k) for k in
              ("family", "construction", "bodies", "size", "pressure", "design",
               "control", "controller", "orientation", "failsafe", "existing_type")}

    # Validate basic field codes against the maps.
    if family not in config.get("family_map", {}):
        add_validation_issue(validation_issues, labels["family"],
                             f"{family} is not a valid Upgrade Kit family (use C2U or TXU).")
    if parsed_model.qty_char not in config.get("bodies_map", {}):
        add_validation_issue(validation_issues, labels["bodies"],
                             f"{parsed_model.qty_char} is not a valid Bodies code (use 1 or 2).")
    if parsed_model.size_code not in config.get("size_map", {}):
        add_validation_issue(validation_issues, labels["size"],
                             f"{parsed_model.size_code} is not a valid Size code.")
    if parsed_model.pressure not in config.get("pressure_map", {}):
        add_validation_issue(validation_issues, labels["pressure"],
                             f"{parsed_model.pressure} is not a valid Pressure code.")
    if parsed_model.control_type not in config.get("control_map", {}):
        add_validation_issue(validation_issues, labels["control"],
                             f"{parsed_model.control_type} is not a valid Control Type.")
    if parsed_model.controller not in config.get("controller_map", {}):
        add_validation_issue(validation_issues, labels["controller"],
                             f"{parsed_model.controller} is not a valid Controller code.")
    if parsed_model.failsafe not in config.get("failsafe_map", {}):
        add_validation_issue(validation_issues, labels["failsafe"],
                             f"{parsed_model.failsafe} is not a valid Failsafe code.")
    if parsed_model.existing_type not in config.get("existing_type_map", {}):
        add_validation_issue(validation_issues, labels["existing_type"],
                             f"{parsed_model.existing_type} is not a valid Existing Valve Type.")
    for opt in parsed_model.options:
        if opt not in config.get("option_map", {}):
            add_validation_issue(validation_issues, "Options",
                                 f"{opt} is not a valid Upgrade Kit option.")

    # Note 2: TXU cannot be ordered with NBF or [Size 14 + NBG].
    if family == "TXU":
        if parsed_model.existing_type == "NBF":
            add_validation_issue(validation_issues, labels["existing_type"],
                                 "TXU cannot be ordered with Existing Type NBF (Note 2).")
        if parsed_model.size_code == "14" and parsed_model.existing_type == "NBG":
            add_validation_issue(validation_issues, labels["existing_type"],
                                 "TXU 14\" cannot be ordered with Existing Type NBG (Note 2).")

    # Note 4: Single (Bodies = 1) requires BC1 or NB1.
    if parsed_model.qty_char == "1" and parsed_model.existing_type not in ("BC1", "NB1"):
        add_validation_issue(validation_issues, labels["existing_type"],
                             "Single body upgrade requires Existing Type BC1 or NB1 (Note 4).")

    # Note 6: Dual (Bodies = 2) requires BCA-E, NBF, or NBG.
    if parsed_model.qty_char == "2" and parsed_model.existing_type not in ("BCA", "BCB", "BCC", "BCD", "BCE", "NBF", "NBG"):
        add_validation_issue(validation_issues, labels["existing_type"],
                             "Dual upgrade requires Existing Type BCA-E, NBF, or NBG (Note 6).")

    # Note 9: Size 14 cannot have Control N, nor Existing Type BCA/BCB/BCC/BCD/NBF.
    if parsed_model.size_code == "14":
        if parsed_model.control_type == "N":
            add_validation_issue(validation_issues, labels["control"],
                                 "14-inch upgrade cannot use Control N (Note 9).")
        if parsed_model.existing_type in ("BCA", "BCB", "BCC", "BCD", "NBF"):
            add_validation_issue(validation_issues, labels["existing_type"],
                                 "14-inch upgrade not available with Existing Type BCA-D or NBF (Note 9).")

    # Note 10: Celeris hood (Designation H) cannot have Control I.
    if family == "C2U" and parsed_model.controller == "H" and parsed_model.control_type == "I":
        add_validation_issue(validation_issues, labels["control"],
                             "Celeris hood (Designation H) cannot use Control I (Note 10).")

    # Note 11: Control I cannot have Failsafe C or O.
    if parsed_model.control_type == "I" and parsed_model.failsafe in ("C", "O"):
        add_validation_issue(validation_issues, labels["failsafe"],
                             "Control I cannot have Failsafe C or O (Note 11).")

    # Note 12: Control N cannot have Failsafe Z.
    if parsed_model.control_type == "N" and parsed_model.failsafe == "Z":
        add_validation_issue(validation_issues, labels["failsafe"],
                             "Control N cannot have Failsafe Z (Note 12).")

    # Note 14: Designation H cannot have option VPL.
    if parsed_model.controller == "H" and "VPL" in parsed_model.options:
        add_validation_issue(validation_issues, "Options",
                             "Designation H cannot have Option VPL (Note 14).")

    # Note 19: Existing Type NBF requires Family = C2U.
    if parsed_model.existing_type == "NBF" and family != "C2U":
        add_validation_issue(validation_issues, labels["existing_type"],
                             "Existing Type NBF only with Family C2U (Note 19).")

    # Note 20: Existing Type NBF cannot have Size 14.
    if parsed_model.existing_type == "NBF" and parsed_model.size_code == "14":
        add_validation_issue(validation_issues, labels["size"],
                             "Existing Type NBF cannot be ordered in Size 14 (Note 20).")

    # TXU restrictions: TXU does not use Designations E or H, nor Controls M or N.
    if family == "TXU":
        if parsed_model.controller in ("E", "H"):
            add_validation_issue(validation_issues, labels["controller"],
                                 "TXU does not use Designations E or H (those are C2 only).")
        if parsed_model.control_type in ("M", "N"):
            add_validation_issue(validation_issues, labels["control"],
                                 "TXU does not use Control M or N (those are C2 only).")


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

    if parsed_model.product_line in ("CELERIS_II", "THERIS", "THERIS_FLEX", "TRACCEL", "VENTURIAN", "BASE_UPGRADEABLE_TIERED", "BASE_UPGRADEABLE_CV"):
        title = f"{PRODUCT_DISPLAY_NAMES[parsed_model.product_line]} {table_spec['title_suffix']}"
        return build_table(title, table_spec["drop"], table_spec["data"], table_spec["show_standard_note"])

    return build_table(table_spec["title"], table_spec["drop"], table_spec["data"], table_spec["show_standard_note"])


def get_product_table_structured(parsed_model: ParsedModel) -> OperatingTable | None:
    table_spec = _table_spec_for(parsed_model)
    if not table_spec:
        return None

    if parsed_model.product_line in ("CELERIS_II", "THERIS", "THERIS_FLEX", "TRACCEL", "VENTURIAN", "BASE_UPGRADEABLE_TIERED", "BASE_UPGRADEABLE_CV"):
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
    if parsed_model.size_code == "08" and parsed_model.design_char in ("S", "L"):
        note_lines.append(notes_theris["08"])
    if parsed_model.size_code == "14" and parsed_model.pressure == "M" and parsed_model.design_char == "L":
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


notes_theris_flex = {
    "1": "Note 1: Flex exhaust (FEV) limited to Controller Designations C, D, N, V.",
    "2": "Note 2: Flex supply (FSV) limited to Controller Designations A, C, D, V.",
    "3": "Note 3: Supply valves provided with insulation, unless ordered with Option = IBO.",
    "4": "Note 4: Size 06 NOT available with Range = L or Orientation = D.",
    "5": "Note 5: Controller Designations C, D, V are individually-commanded units that generate flow feedback signals. No tracking ability.",
    "6": "Note 6: Controller Designation V command and feedback signals can either be 2-10 Vdc or BACnet inputs and outputs.",
    "9": "Note 9: Option PSL pressure switch trips at 0.3\" WC for Range = M and 0.2\" WC for Range = L.",
    "10": "Note 10: Option REI remote electronics, INDOOR installations. Limited to 150 ft (45.7 m) of 22 gauge cable for low-speed electric actuators (Control = H, L).",
    "11": "Note 11: Options SFB, SFD, and SFI cannot be ordered with each other.",
}


def build_theris_flex_notes(parsed_model: ParsedModel, include_table_text: bool = True) -> list[str]:
    note_lines: list[str] = []
    if parsed_model.prefix == "FEV":
        note_lines.append(notes_theris_flex["1"])
    if parsed_model.prefix == "FSV":
        note_lines.append(notes_theris_flex["2"])
        if "IBO" not in parsed_model.options:
            note_lines.append(notes_theris_flex["3"])
    if parsed_model.size_code == "06":
        note_lines.append(notes_theris_flex["4"])
    if parsed_model.controller in ("C", "D", "V"):
        note_lines.append(notes_theris_flex["5"])
    if parsed_model.controller == "V":
        note_lines.append(notes_theris_flex["6"])
    if "PSL" in parsed_model.options:
        note_lines.append(notes_theris_flex["9"])
    if "REI" in parsed_model.options:
        note_lines.append(notes_theris_flex["10"])
    if any(o in parsed_model.options for o in ("SFB", "SFD", "SFI")):
        note_lines.append(notes_theris_flex["11"])
    _append_product_table_note(note_lines, parsed_model, include_table_text)
    return note_lines


def build_traccel_notes(parsed_model: ParsedModel, include_table_text: bool = True) -> list[str]:
    note_lines: list[str] = []
    _append_shared_weather_notes(note_lines, parsed_model)
    _append_product_table_note(note_lines, parsed_model, include_table_text)
    return note_lines


notes_venturian = {
    "1":  "Note 1: All supply valves (VSV) are provided standard with insulation.",
    "5":  "Note 5: Pressure switch alarm setpoint: 0.3\" WC for medium pressure / 0.2\" WC for low pressure.",
    "6":  "Note 6: Low pressure (Range = L) shut-off valves (Design = S) are NOT available in vertical up flow (Orientation = U).",
    "7":  "Note 7: Valve Design A is mandatory on constant volume valves (Control Type = C).",
    "9":  "Note 9: Control Type L is mandatory on single 14-inch and dual VAV valves.",
    "10": "Note 10: Control Type H is only available on 8/10/12-inch single VAV valves.",
    "11": "Note 11: Option EVI is ONLY available on exhaust valves (VEV).",
    "12": "Note 12: Option IBO available on exhaust and supply valves (VEV and VSV).",
    "13": "Note 13: Options SFB, SFD, and SFI cannot be ordered with Bodies F or 2.",
    "14": "Note 14: Valve Design A and Designation N are mandatory on constant volume valves.",
    "17": "Note 17: Designations B and D only available on non-shut-off valves (Design = A).",
    "18": "Note 18: Designation D is ONLY available on supply valves (VSV).",
}


def build_venturian_notes(parsed_model: ParsedModel, include_table_text: bool = True) -> list[str]:
    note_lines: list[str] = []
    if parsed_model.prefix == "VSV":
        note_lines.append(notes_venturian["1"])
    if "PSL" in parsed_model.options:
        note_lines.append(notes_venturian["5"])
    if parsed_model.pressure == "L" and parsed_model.design_char == "S":
        note_lines.append(notes_venturian["6"])
    if parsed_model.control_type == "C":
        note_lines.append(notes_venturian["7"])
        note_lines.append(notes_venturian["14"])
    if parsed_model.size_code == "14" and parsed_model.qty_char == "1":
        note_lines.append(notes_venturian["9"])
    if parsed_model.qty_char == "2":
        note_lines.append(notes_venturian["9"])
    if parsed_model.control_type == "H":
        note_lines.append(notes_venturian["10"])
    if "EVI" in parsed_model.options:
        note_lines.append(notes_venturian["11"])
    if "IBO" in parsed_model.options:
        note_lines.append(notes_venturian["12"])
    if any(o in parsed_model.options for o in ("SFB", "SFD", "SFI")):
        note_lines.append(notes_venturian["13"])
    if parsed_model.controller in ("B", "D"):
        note_lines.append(notes_venturian["17"])
    if parsed_model.controller == "D":
        note_lines.append(notes_venturian["18"])
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


def build_base_upgradeable_tiered_notes(parsed_model: ParsedModel, include_table_text: bool = True) -> list[str]:
    note_lines: list[str] = []
    if parsed_model.prefix == "BSV":
        note_lines.append("Note: Supply valves come standard with insulation and blocks.")
    if parsed_model.construction == "D":
        note_lines.append(notes_base_upgradeable_tiered["1"])
    if parsed_model.qty_char == "F":
        note_lines.append(notes_base_upgradeable_tiered["2"])
    if parsed_model.size_code == "08" and parsed_model.design_char in ("L", "S"):
        note_lines.append(notes_base_upgradeable_tiered["3"])
    if parsed_model.size_code == "14" and parsed_model.pressure == "M" and parsed_model.design_char == "L":
        note_lines.append(notes_base_upgradeable_tiered["4"])
    if parsed_model.size_code == "14" and parsed_model.control_type in ("Q", "S"):
        note_lines.append(notes_base_upgradeable_tiered["5"])
    if "PSL" in parsed_model.options:
        note_lines.append(notes_base_upgradeable_tiered["6"])
    if parsed_model.pressure == "L" and parsed_model.design_char == "L":
        note_lines.append(notes_base_upgradeable_tiered["7"])
    if parsed_model.pressure == "L" and parsed_model.design_char == "S":
        note_lines.append(notes_base_upgradeable_tiered["8"])
    if parsed_model.control_type in ("Q", "S"):
        note_lines.append(notes_base_upgradeable_tiered["9"])
    if parsed_model.control_type == "T":
        note_lines.append(notes_base_upgradeable_tiered["10"])
    if "EVI" in parsed_model.options:
        note_lines.append(notes_base_upgradeable_tiered["11"])
    if "IBO" in parsed_model.options:
        note_lines.append(notes_base_upgradeable_tiered["12"])
    if "REI" in parsed_model.options and parsed_model.control_type in ("Q", "S"):
        note_lines.append(notes_base_upgradeable_tiered["13"])
    if any(opt in parsed_model.options for opt in ("SFB", "SFD", "SFI")):
        note_lines.append(notes_base_upgradeable_tiered["14"])
    _append_product_table_note(note_lines, parsed_model, include_table_text)
    return note_lines


def build_pbc_notes(parsed_model: ParsedModel, include_table_text: bool = True) -> list[str]:
    return ["Note: PBC functions (GEN/ZBH/ZBL) are mutually exclusive — pick exactly one per controller."]


def build_fhd500_notes(parsed_model: ParsedModel, include_table_text: bool = True) -> list[str]:
    return [
        "Note: Option HUV combines HUB + DHV in one part — order either HUV alone, or HUB and DHV separately.",
        "Note: At most one mounting-kit option (RD1, RM1, or RM3) per FHD500.",
    ]


def build_fhd130_notes(parsed_model: ParsedModel, include_table_text: bool = True) -> list[str]:
    note_lines: list[str] = [
        "Note 1: For constant volume and variable frequency drive applications, an LRC100-SCD is also required.",
        "Note 2: FHD Series 130 displays flow or face velocity value plus energy-saving features.",
        # Note 4 surfaces the FHV-mandatory rule for every Sentry order, so the
        # user sees it BEFORE they finalize a model that should have included FHV.
        "Note 4: Option FHV is mandatory for single vertical sash sensors and horizontal sensors with "
        "less than 75\" total bar length. Converts the resistive sash input into a voltage output to the LVC UI1. "
        "Confirm sash configuration before ordering this Sentry FHD without FHV.",
    ]
    if "DHV" in parsed_model.options:
        note_lines.append(
            "Note 3: When option DHV is ordered, the corresponding sash sensor catalog number may need to "
            "change to prevent a duplicate DHV being shipped. Refer to the Sash Sensors with NHV table in the PDS."
        )
    if "FHV" in parsed_model.options:
        note_lines.append("Note 5: Option FHV should NOT be ordered with DHV.")
    return note_lines


def build_zps_notes(parsed_model: ParsedModel, include_table_text: bool = True) -> list[str]:
    return [
        "Note: One ZPS for fume hoods up to 8'; multiple units (up to 4) may be used for larger or "
        "multi-sided hoods.",
    ]


def build_upgrade_kit_notes(parsed_model: ParsedModel, include_table_text: bool = True) -> list[str]:
    note_lines: list[str] = [
        "Note 1: All upgrade valve controller boards require field-generated or factory curve download and validation.",
    ]
    if parsed_model.qty_char == "1" and parsed_model.existing_type == "NB1":
        note_lines.append(
            "Note 5: Single valves with NO BaseChannels can ONLY be upgraded if the original valves have "
            "Accel II conical-shaped diffuser bodies and shipped on or before 08/09/2017."
        )
    if parsed_model.qty_char == "2" and parsed_model.existing_type in ("BCA", "BCB", "BCC", "BCD", "BCE"):
        note_lines.append(
            "Note 7: Dual valves WITH BaseChannels MUST be visually inspected to determine the vintage of the "
            "original valve if it shipped prior to 1/1/1998 or during December 2002."
        )
    if parsed_model.qty_char == "2" and parsed_model.existing_type in ("NBF", "NBG"):
        note_lines.append(
            "Note 8: Dual valves with NO BaseChannels can ONLY be upgraded if the original valves have Accel II "
            "(conical-shaped diffuser) bodies, shipped on or before 08/09/2017, and have been visually inspected "
            "to verify vintage and (for NBG) pivot arm position."
        )
    if parsed_model.existing_type in ("NB1", "NBF", "NBG"):
        note_lines.append(
            "Note 18: Existing No-BaseChannel CxV & PxV valves with hourglass bodies CANNOT be upgraded."
        )
    note_lines.append("Note 22: Base channels were added to CEV/CSV on 08/10/2017.")
    return note_lines


NOTE_BUILDERS = {
    "ANALOG": build_analog_notes,
    "CELERIS_II": build_celeris_notes,
    "THERIS": build_theris_notes,
    "THERIS_FLEX": build_theris_flex_notes,
    "TRACCEL": build_traccel_notes,
    "VENTURIAN": build_venturian_notes,
    "CSCP": build_cscp_notes,
    "BASE_UPGRADEABLE_TIERED": build_base_upgradeable_tiered_notes,
    "BASE_UPGRADEABLE_CV": build_base_upgradeable_cv_notes,
    "PBC": build_pbc_notes,
    "FHD500": build_fhd500_notes,
    "FHD130": build_fhd130_notes,
    "ZPS": build_zps_notes,
    "UPGRADE_KIT": build_upgrade_kit_notes,
}


def build_notes(parsed_model: ParsedModel, include_table_text: bool = True) -> list[str]:
    if parsed_model.product_line == "UNKNOWN":
        return []
    note_builder = NOTE_BUILDERS.get(parsed_model.product_line)
    if not note_builder:
        return []
    return list(dict.fromkeys(note_builder(parsed_model, include_table_text=include_table_text)))


def process_model(full_model: str, analog_active: bool = False) -> tuple[bool, str, dict, list, list, "ParsedModel | None"]:
    ok, warnings, parsed_model = parse_model(full_model, analog_active)
    if not ok or parsed_model is None:
        return False, _summarize_warnings(warnings), {}, [], [], None

    decoded_fields = decode_model(parsed_model)
    note_lines = build_notes(parsed_model, include_table_text=True)
    validation_issues = validate_model(parsed_model)
    _apply_structural_warnings(parsed_model, warnings, validation_issues)
    validation_issues = dedupe_validation_issues(validation_issues)

    return True, _summarize_warnings(warnings), decoded_fields, note_lines, validation_issues, parsed_model


def process_model_structured(
    full_model: str,
    analog_active: bool = False,
) -> tuple[bool, str, dict, list, list, "ParsedModel | None", "OperatingTable | None"]:
    ok, warnings, parsed_model = parse_model(full_model, analog_active)
    if not ok or parsed_model is None:
        return False, _summarize_warnings(warnings), {}, [], [], None, None

    decoded_fields = decode_model(parsed_model)
    note_lines = build_notes(parsed_model, include_table_text=False)
    validation_issues = validate_model(parsed_model)
    _apply_structural_warnings(parsed_model, warnings, validation_issues)
    validation_issues = dedupe_validation_issues(validation_issues)
    operating_table = get_product_table_structured(parsed_model)

    return True, _summarize_warnings(warnings), decoded_fields, note_lines, validation_issues, parsed_model, operating_table


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
        ("EXVA108M-ANHHO-PSL", False),
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