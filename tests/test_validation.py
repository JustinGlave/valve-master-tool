"""
Regression tests for phoenix_master_backend.process_model_structured.

Run with:
    python -m unittest discover -s tests
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phoenix_master_backend import process_model_structured


def _decode(model: str, analog: bool = False):
    ok, msg, decoded, notes, issues, parsed, table = process_model_structured(model, analog)
    return ok, msg, decoded, notes, issues, parsed, table


class ValidationTestCase(unittest.TestCase):
    def assertValid(self, model: str, analog: bool = False) -> None:
        ok, _, _, _, issues, _, _ = _decode(model, analog)
        self.assertTrue(ok, f"parse failed for {model}")
        self.assertEqual(issues, [], f"{model} should be valid; got {issues}")

    def assertHasIssue(self, model: str, field: str, analog: bool = False) -> None:
        ok, _, _, _, issues, _, _ = _decode(model, analog)
        self.assertTrue(ok, f"parse failed for {model}")
        fields = [i["field"] for i in issues]
        self.assertIn(field, fields, f"{model}: expected an issue on '{field}', got {issues}")

    def assertHasAnyIssue(self, model: str, analog: bool = False) -> None:
        ok, _, _, _, issues, _, _ = _decode(model, analog)
        self.assertTrue(ok, f"parse failed for {model}")
        self.assertGreater(len(issues), 0, f"{model}: expected at least one issue")


class ValidModelsTests(ValidationTestCase):
    """Models from the GUI's VALID_TEST_MODELS list — must remain valid."""

    def test_celeris_mav_high_speed_with_rei(self) -> None:
        self.assertValid("MAVA108M-AMEHZ-REI")

    def test_celeris_exv_pneumatic_hood(self) -> None:
        # PSL (pressure switch low limit) is documented; "P" was a phantom option
        # cleaned out as part of the PDS p.12 alignment.
        self.assertValid("EXVA108M-ANHHO-PSL")

    def test_theris_8in_low_pressure_standard_lonmark_with_wre(self) -> None:
        # Controller E is LonMark — WRE is permitted there.
        self.assertValid("HEVA108L-SIEHZ-WRE")


class FailingModelsTests(ValidationTestCase):
    """Models from the GUI's FAILING_TEST_MODELS list — must remain failing."""

    def test_mav_low_speed_hood_controller_invalid(self) -> None:
        self.assertHasAnyIssue("MAVA114L-ALHHZ")

    def test_celeris_d_construction_dual_with_sfb(self) -> None:
        self.assertHasAnyIssue("MAVD208M-AAEHN-SFB")

    def test_base_upgradeable_low_pressure_low_leakage(self) -> None:
        self.assertHasAnyIssue("BEVA108L-LQFHZ")


class TherisRulesTests(ValidationTestCase):
    """New Theris validation rules from notes_theris."""

    def test_8in_shutoff_S_requires_construction_a(self) -> None:
        self.assertHasIssue("HSVB108L-SIAHZ", "Construction")

    def test_8in_shutoff_L_requires_construction_a(self) -> None:
        self.assertHasIssue("HSVB108L-LIAHZ", "Construction")

    def test_theris_construction_b_is_invalid(self) -> None:
        # Theris is offered in Construction A only per MKT-0228, so any model
        # with construction B should fail validation regardless of size/design.
        self.assertHasIssue("HSVB108L-AIAHZ", "Construction")

    def test_14in_medium_low_leakage_unavailable(self) -> None:
        self.assertHasIssue("HSVA114M-LIAHZ", "Valve Design")

    def test_14in_medium_standard_is_valid(self) -> None:
        # Same size+pressure but design S — rule does not apply.
        ok, _, _, _, issues, _, _ = _decode("HSVA114M-SIAHZ")
        self.assertTrue(ok)
        design_issues = [i for i in issues if i["field"] == "Valve Design"]
        self.assertEqual(design_issues, [])

    def test_low_pressure_low_leakage_unavailable_size_10(self) -> None:
        self.assertHasIssue("HSVA110L-LIAHZ", "Valve Design")

    def test_low_pressure_low_leakage_unavailable_size_12(self) -> None:
        self.assertHasIssue("HSVA112L-LIAHZ", "Valve Design")

    def test_low_pressure_standard_no_upflow(self) -> None:
        self.assertHasIssue("HSVA110L-SIAUZ", "Orientation")

    def test_low_pressure_standard_horizontal_is_valid(self) -> None:
        ok, _, _, _, issues, _, _ = _decode("HSVA110L-SIAHZ")
        self.assertTrue(ok)
        orient_issues = [i for i in issues if i["field"] == "Orientation"]
        self.assertEqual(orient_issues, [])

    def test_wre_with_bacnet_controller_invalid(self) -> None:
        # Controller A is BACnet — WRE is documented as LonMark-only.
        self.assertHasIssue("HSVA110L-SIAHZ-WRE", "Options")

    def test_wre_with_lonmark_controller_e_valid(self) -> None:
        ok, _, _, _, issues, _, _ = _decode("HSVA110L-SIEHZ-WRE")
        self.assertTrue(ok)
        opt_issues = [i for i in issues if i["field"] == "Options"]
        self.assertEqual(opt_issues, [])

    def test_invalid_options_are_rejected(self) -> None:
        # The pre-correction option_map had B/F/M/P/O/R/T/REO/SFX — none of
        # which appear in the published ordering guide. Spot-check that the
        # cleanup actually rejects them now.
        self.assertHasIssue("HSVA108L-SIEHZ-REO", "Options")

    def test_bodies_3_or_4_is_invalid(self) -> None:
        # Theris is offered only as F/1/2 per MKT-0228. Triple/quad don't exist.
        self.assertHasIssue("HSVA310L-SIAHZ", "Bodies")
        self.assertHasIssue("HSVA410L-SIAHZ", "Bodies")

    def test_bodies_2_size_08_invalid(self) -> None:
        # Bodies = 2 is "10\", 12\", 14\" only" per all 4 ordering guides.
        self.assertHasIssue("HSVA208M-AIAHZ", "Bodies")

    def test_bodies_2_size_10_valid(self) -> None:
        ok, _, _, _, issues, _, _ = _decode("HSVA210M-AIAHZ")
        self.assertTrue(ok)
        body_issues = [i for i in issues if i["field"] == "Bodies"]
        self.assertEqual(body_issues, [])

    def test_wre_horizontal_only(self) -> None:
        # WRE requires horizontal orientation per MKT-0118 Note 6.
        self.assertHasIssue("HSVA110L-SIEUZ-WRE", "Options")

    def test_wre_excludes_control_h(self) -> None:
        # WRE requires IP54/IP56 actuator (Control Type I or L), not NEMA-1 H.
        self.assertHasIssue("HSVA110L-SHEHZ-WRE", "Options")


class TraccelRulesTests(ValidationTestCase):
    """Traccel uses the same 4 structural rules as Theris (MKT-0242 mirrors
    MKT-0228) plus the WRE-LonMark constraint."""

    def test_8in_shutoff_S_with_construction_b_invalid(self) -> None:
        # Traccel offers construction B; the rule actively excludes it at 8" S/L.
        self.assertHasIssue("TSVB108L-SIAHZ", "Construction")

    def test_8in_shutoff_L_with_construction_b_invalid(self) -> None:
        self.assertHasIssue("TSVB108L-LIAHZ", "Construction")

    def test_14in_medium_low_leakage_unavailable(self) -> None:
        self.assertHasIssue("TSVA114M-LIAHZ", "Valve Design")

    def test_low_pressure_low_leakage_unavailable(self) -> None:
        self.assertHasIssue("TSVA110L-LIAHZ", "Valve Design")

    def test_low_pressure_standard_no_upflow(self) -> None:
        self.assertHasIssue("TSVA110L-SIAUZ", "Orientation")

    def test_low_pressure_standard_horizontal_is_valid(self) -> None:
        ok, _, _, _, issues, _, _ = _decode("TSVA110L-SIAHZ")
        self.assertTrue(ok)
        orient_issues = [i for i in issues if i["field"] == "Orientation"]
        self.assertEqual(orient_issues, [])

    def test_wre_with_bacnet_controller_invalid(self) -> None:
        self.assertHasIssue("TSVA110L-SIAHZ-WRE", "Options")

    def test_wre_with_lonmark_controller_x_valid(self) -> None:
        ok, _, _, _, issues, _, _ = _decode("TSVA110L-SIXHZ-WRE")
        self.assertTrue(ok)
        opt_issues = [i for i in issues if i["field"] == "Options"]
        self.assertEqual(opt_issues, [])

    def test_bodies_3_or_4_is_invalid(self) -> None:
        # Per MKT-0242 / MKT-0041, Traccel bodies are F/1/2 only.
        self.assertHasIssue("TSVA310M-AIAHZ", "Bodies")
        self.assertHasIssue("TSVA410M-AIAHZ", "Bodies")

    def test_bodies_2_size_08_invalid(self) -> None:
        self.assertHasIssue("TSVA208M-AIAHZ", "Bodies")

    def test_bodies_2_size_12_valid(self) -> None:
        ok, _, _, _, issues, _, _ = _decode("TSVA212M-AIAHZ")
        self.assertTrue(ok)
        body_issues = [i for i in issues if i["field"] == "Bodies"]
        self.assertEqual(body_issues, [])

    def test_wre_horizontal_only(self) -> None:
        # WRE requires horizontal orientation per MKT-0041 Note 6.
        self.assertHasIssue("TSVA110L-SIEUZ-WRE", "Options")

    def test_wre_excludes_control_h(self) -> None:
        self.assertHasIssue("TSVA110L-SHEHZ-WRE", "Options")

    def test_control_h_with_lonmark_controller_invalid(self) -> None:
        # Control H is BACnet-only on Traccel; LonMark guide MKT-0041 omits H.
        self.assertHasIssue("TSVA110M-AHEHZ", "Control Type")

    def test_control_h_with_bacnet_controller_valid(self) -> None:
        # Control H + BACnet controller A is fine.
        ok, _, _, _, issues, _, _ = _decode("TSVA110M-AHAHZ")
        self.assertTrue(ok)
        ct_issues = [i for i in issues if i["field"] == "Control Type"]
        self.assertEqual(ct_issues, [])


class PBCRulesTests(ValidationTestCase):
    """PBC: PBC[series]-[function] per PDS p.11 — Phase F."""

    def test_routes_to_pbc(self) -> None:
        from phoenix_master_backend import detect_product_line
        self.assertEqual(detect_product_line("PBC500-ZBH"), "PBC")

    def test_basic_valid(self) -> None:
        ok, _, _, _, issues, _, _ = _decode("PBC500-ZBH")
        self.assertTrue(ok)
        self.assertEqual(issues, [])

    def test_all_series_valid(self) -> None:
        for s in ("500", "501", "504", "505"):
            ok, _, _, _, issues, _, _ = _decode(f"PBC{s}-GEN")
            series_issues = [i for i in issues if "series" in i["message"].lower()]
            self.assertEqual(series_issues, [], f"Series {s} should be valid; got {issues}")

    def test_invalid_series(self) -> None:
        self.assertHasIssue("PBC502-GEN", "Series")

    def test_invalid_function(self) -> None:
        self.assertHasIssue("PBC500-XYZ", "Function")

    def test_missing_function(self) -> None:
        self.assertHasIssue("PBC500", "Function")


class FHD500RulesTests(ValidationTestCase):
    """FHD500 per PDS p.56 — Phase G."""

    def test_routes_to_fhd500(self) -> None:
        from phoenix_master_backend import detect_product_line
        self.assertEqual(detect_product_line("FHD500-DHV"), "FHD500")

    def test_basic_valid(self) -> None:
        ok, _, _, _, issues, _, _ = _decode("FHD500-DHV")
        self.assertTrue(ok)
        self.assertEqual(issues, [])

    def test_dhv_and_hub_mutually_exclusive(self) -> None:
        # Per user direction: only one of DHV/HUB/HUV per FHD500.
        self.assertHasIssue("FHD500-DHV-HUB", "Options")

    def test_two_mounting_kits_invalid(self) -> None:
        self.assertHasIssue("FHD500-RD1-RM1", "Options")

    def test_huv_alone_valid(self) -> None:
        ok, _, _, _, issues, _, _ = _decode("FHD500-HUV")
        self.assertTrue(ok)
        self.assertEqual(issues, [])

    def test_huv_with_one_mounting_valid(self) -> None:
        ok, _, _, _, issues, _, _ = _decode("FHD500-HUV-RD1")
        self.assertTrue(ok)
        self.assertEqual(issues, [])


class FHD130RulesTests(ValidationTestCase):
    """Sentry FHD130 per PDS p.57 — Phase H."""

    def test_routes_to_fhd130(self) -> None:
        from phoenix_master_backend import detect_product_line
        self.assertEqual(detect_product_line("FHD130-ENG-RD1"), "FHD130")

    def test_basic_valid(self) -> None:
        ok, _, _, _, issues, _, _ = _decode("FHD130-ENG-RD1")
        self.assertTrue(ok)
        self.assertEqual(issues, [])

    def test_invalid_language(self) -> None:
        self.assertHasIssue("FHD130-ESP-RD1", "Language")

    def test_dhv_requires_hub(self) -> None:
        # Note 3.
        self.assertHasIssue("FHD130-ENG-DHV", "Options")

    def test_dhv_with_hub_valid(self) -> None:
        ok, _, _, _, issues, _, _ = _decode("FHD130-ENG-DHV-HUB")
        self.assertTrue(ok)
        self.assertEqual(issues, [])

    def test_dhv_and_fhv_mutually_exclusive(self) -> None:
        # Note 5.
        self.assertHasIssue("FHD130-ENG-DHV-HUB-FHV", "Options")


class ZPSRulesTests(ValidationTestCase):
    """ZPS per PDS p.58 — Phase I."""

    def test_routes_to_zps(self) -> None:
        from phoenix_master_backend import detect_product_line
        self.assertEqual(detect_product_line("ZPS310"), "ZPS")

    def test_all_module_counts_valid(self) -> None:
        for mc in ("10", "20", "30", "40"):
            ok, _, _, _, issues, _, _ = _decode(f"ZPS3{mc}")
            self.assertEqual(issues, [], f"Module count {mc} should be valid; got {issues}")

    def test_invalid_module_count(self) -> None:
        self.assertHasIssue("ZPS399", "Number of Modules")

    def test_invalid_series(self) -> None:
        self.assertHasIssue("ZPS210", "Series")


class UpgradeKitRulesTests(ValidationTestCase):
    """Upgrade Kits per PDS p.54 — Phase J."""

    def test_routes_to_upgrade_kit(self) -> None:
        from phoenix_master_backend import detect_product_line
        self.assertEqual(detect_product_line("C2UX112L-XMEXO-BC1"), "UPGRADE_KIT")
        self.assertEqual(detect_product_line("TXUX110M-XIXXZ-BCA"), "UPGRADE_KIT")

    def test_c2u_basic_valid(self) -> None:
        ok, _, _, _, issues, _, _ = _decode("C2UX112L-XMEXO-BC1")
        self.assertTrue(ok)
        self.assertEqual(issues, [])

    def test_txu_with_nbf_invalid(self) -> None:
        # Note 2.
        self.assertHasIssue("TXUX110M-XIXXZ-NBF", "Existing Valve Type")

    def test_single_requires_bc1_or_nb1(self) -> None:
        # Note 4.
        self.assertHasIssue("C2UX112L-XMEXO-BCA", "Existing Valve Type")

    def test_dual_requires_dual_existing_type(self) -> None:
        # Note 6.
        self.assertHasIssue("C2UX212L-XMEXO-BC1", "Existing Valve Type")

    def test_size_14_no_control_n(self) -> None:
        # Note 9.
        self.assertHasIssue("C2UX114M-XNEXO-BC1", "Control Type")

    def test_control_i_no_failsafe_c(self) -> None:
        # Note 11.
        self.assertHasIssue("C2UX112L-XIEXC-BC1", "Fail-Safe Position")

    def test_designation_h_no_vpl(self) -> None:
        # Note 14.
        self.assertHasIssue("C2UX112L-XMHXO-BC1-VPL", "Options")

    def test_txu_no_designation_e(self) -> None:
        self.assertHasIssue("TXUX112L-XIEXZ-BCA", "Valve Controller Designation")

    def test_nbf_only_with_c2u(self) -> None:
        # Note 19 (C2UX with NBF dual valid).
        ok, _, _, _, issues, _, _ = _decode("C2UX212L-XMEXO-NBF")
        et_issues = [i for i in issues if i["field"] == "Existing Valve Type"]
        self.assertEqual(et_issues, [])


class VenturianRulesTests(ValidationTestCase):
    """Venturian rules per PDS p.31 — Phase C."""

    def test_vsv_routes_to_venturian(self) -> None:
        from phoenix_master_backend import detect_product_line
        self.assertEqual(detect_product_line("VSVA108M-AHAHZ"), "VENTURIAN")

    def test_vev_routes_to_venturian(self) -> None:
        from phoenix_master_backend import detect_product_line
        self.assertEqual(detect_product_line("VEVA108M-AHAHZ"), "VENTURIAN")

    def test_basic_valid(self) -> None:
        ok, _, _, _, issues, _, _ = _decode("VEVA108M-AHAHZ")
        self.assertTrue(ok)
        self.assertEqual(issues, [])

    def test_dual_size_08_invalid(self) -> None:
        # Size 08 is single-body only.
        self.assertHasIssue("VEVA208M-ALAHZ", "Number of Valve Bodies")

    def test_dual_requires_control_l(self) -> None:
        # Note 9: dual valves require Control = L.
        self.assertHasIssue("VEVA210M-AHAHZ", "Control Type")

    def test_size_14_single_requires_control_l(self) -> None:
        # Note 9: single 14" requires Control = L.
        self.assertHasIssue("VEVA114M-AHAHZ", "Control Type")

    def test_constant_volume_requires_design_a(self) -> None:
        # Note 7: Control C → Design A.
        self.assertHasIssue("VEVA108M-SCNHZ", "Valve Design")

    def test_constant_volume_requires_controller_n(self) -> None:
        # Note 14.
        self.assertHasIssue("VEVA108M-ACDHZ", "Valve Controller Designation")

    def test_control_h_size_14_invalid(self) -> None:
        # Note 10: Control H limited to 8/10/12.
        self.assertHasIssue("VEVA114M-AHAHZ", "Valve Size")

    def test_low_pressure_shutoff_no_upflow(self) -> None:
        # Note 6.
        self.assertHasIssue("VEVA110L-SLAUZ", "Valve Orientation")

    def test_evi_only_on_exhaust(self) -> None:
        # Note 11.
        self.assertHasIssue("VSVA108M-AHAHZ-EVI", "Options")

    def test_designation_d_supply_only(self) -> None:
        # Note 18: D = TP, supply only.
        self.assertHasIssue("VEVA110M-ALDHZ", "Valve Controller Designation")

    def test_designations_b_d_non_shutoff_only(self) -> None:
        # Note 17: B and D require Design A.
        self.assertHasIssue("VSVA110M-SLDHZ", "Valve Controller Designation")

    def test_sfb_with_dual_invalid(self) -> None:
        # Note 13: SFB/SFD/SFI cannot be ordered with Bodies F or 2.
        self.assertHasIssue("VEVA210M-ALAHZ-SFB", "Options")


class TherisFlexRulesTests(ValidationTestCase):
    """Theris FLEX rules per PDS p.24 — Phase B."""

    def test_fsv_routes_to_flex(self) -> None:
        from phoenix_master_backend import detect_product_line
        self.assertEqual(detect_product_line("FSVA108M-AHAHZ"), "THERIS_FLEX")

    def test_fev_routes_to_flex(self) -> None:
        from phoenix_master_backend import detect_product_line
        self.assertEqual(detect_product_line("FEVA108M-ALCHZ"), "THERIS_FLEX")

    def test_fsv_basic_valid(self) -> None:
        # FSV with controller A (TP supply) is allowed (Note 2).
        ok, _, _, _, issues, _, _ = _decode("FSVA108M-AHAHZ-PSL")
        self.assertTrue(ok)
        self.assertEqual(issues, [])

    def test_fev_with_controller_a_invalid(self) -> None:
        # Note 1: FEV is restricted to {C, D, N, V}; A is not valid.
        self.assertHasIssue("FEVA108M-AHAHZ", "BACnet Controller Designation")

    def test_fsv_with_controller_n_invalid(self) -> None:
        # Note 2: FSV is restricted to {A, C, D, V}; N is not valid.
        self.assertHasIssue("FSVA108M-AHNHZ", "BACnet Controller Designation")

    def test_size_06_low_pressure_invalid(self) -> None:
        # Note 4.
        self.assertHasIssue("FSVA106L-ALAHZ", "Pressure Range")

    def test_size_06_vertical_down_invalid(self) -> None:
        # Note 4.
        self.assertHasIssue("FSVA106M-ALADZ", "Orientation")

    def test_size_06_medium_horizontal_valid(self) -> None:
        ok, _, _, _, issues, _, _ = _decode("FSVA106M-ALAHZ")
        self.assertTrue(ok)
        self.assertEqual(issues, [])

    def test_evi_only_on_fev(self) -> None:
        # Note 7: EVI is exhaust-only.
        self.assertHasIssue("FSVA108M-AHAHZ-EVI", "Options")

    def test_evi_and_ibo_mutually_exclusive(self) -> None:
        self.assertHasIssue("FEVA108M-ALCHZ-EVI-IBO", "Options")

    def test_sfb_sfd_mutually_exclusive(self) -> None:
        self.assertHasIssue("FSVA108M-AHAHZ-SFB-SFD", "Options")


class BaseUpgradeableCVRulesTests(ValidationTestCase):
    """Constant Volume / Base Upgradeable rules per PDS p.34 — Phase D split."""

    def test_csv_routes_to_cv_variant(self) -> None:
        from phoenix_master_backend import detect_product_line
        self.assertEqual(detect_product_line("CSVA110M-ACNHZ"), "BASE_UPGRADEABLE_CV")

    def test_cev_routes_to_cv_variant(self) -> None:
        from phoenix_master_backend import detect_product_line
        self.assertEqual(detect_product_line("CEVA112M-ACNHZ"), "BASE_UPGRADEABLE_CV")

    def test_bxv_with_cv_control_routes_to_cv(self) -> None:
        from phoenix_master_backend import detect_product_line
        # Control H is in CV's control set → CV variant.
        self.assertEqual(detect_product_line("BEVA110M-AHFHZ"), "BASE_UPGRADEABLE_CV")
        # Control B (pneumatic) is also CV.
        self.assertEqual(detect_product_line("BEVA110M-ABFCZ"), "BASE_UPGRADEABLE_CV")

    def test_bxv_with_tiered_control_routes_to_tiered(self) -> None:
        from phoenix_master_backend import detect_product_line
        # Q control type stays on the Tiered variant.
        self.assertEqual(detect_product_line("BEVA108L-LQFHZ"), "BASE_UPGRADEABLE_TIERED")
        # T control type also routes to Tiered.
        self.assertEqual(detect_product_line("BEVA110M-ATFCZ"), "BASE_UPGRADEABLE_TIERED")

    def test_csv_design_must_be_a(self) -> None:
        # Note 1: CV valves are Design A only.
        self.assertHasIssue("CSVA110M-SCNHZ", "Valve Design")

    def test_csv_control_must_be_c(self) -> None:
        # CSV/CEV require Control = C.
        self.assertHasIssue("CSVA110M-AHNHZ", "Control Type")

    def test_bxv_cannot_use_control_c(self) -> None:
        # Control C is reserved for CSV/CEV.
        self.assertHasIssue("BEVA110M-ACNHZ", "Control Type")

    def test_8in_shutoff_requires_construction_a(self) -> None:
        # Note 3: 8" shut-off (L or S) → Construction A only.
        self.assertHasIssue("BEVB108M-LIFHZ", "Valve Construction")

    def test_14in_medium_low_leakage_unavailable(self) -> None:
        # Note 4: 14" + M + L unavailable.
        self.assertHasIssue("BEVA114M-LIFHZ", "Valve Design")

    def test_low_pressure_low_leakage_unavailable(self) -> None:
        # Note 6.
        self.assertHasIssue("BEVA110L-LIFHZ", "Valve Design")

    def test_low_pressure_standard_no_upflow(self) -> None:
        # Note 7.
        self.assertHasIssue("BEVA110L-SIFUZ", "Valve Orientation")

    def test_control_h_requires_flow_feedback(self) -> None:
        # Note 8: H or L → Controller = F.
        self.assertHasIssue("BEVA110M-AHNHZ", "Valve Controller Designation")

    def test_control_l_requires_flow_feedback(self) -> None:
        self.assertHasIssue("BEVA110M-ALNHZ", "Valve Controller Designation")

    def test_failsafe_c_requires_control_b(self) -> None:
        # C/O failsafe is only valid with Control B (pneumatic).
        self.assertHasIssue("BEVA110M-AHFHC", "Fail-Safe Position")

    def test_failsafe_z_invalid_for_pneumatic(self) -> None:
        # Control B requires C or O failsafe, not Z.
        self.assertHasIssue("BEVA110M-ABFHZ", "Fail-Safe Position")

    def test_reo_requires_pneumatic(self) -> None:
        # Note 11: REO → Control B + Controller F + Horizontal.
        self.assertHasIssue("BEVA110M-AHFHZ-REO", "Options")

    def test_rei_requires_flow_feedback(self) -> None:
        # Note 10: REI → Controller F.
        self.assertHasIssue("BEVA110M-AINHZ-REI", "Options")

    def test_sfb_requires_single_body(self) -> None:
        # Note 12: SFB/SFD/SFI → Bodies = 1.
        self.assertHasIssue("BEVA210M-AHFHZ-SFB", "Options")

    def test_vpo_requires_b_or_f_control(self) -> None:
        # Note 13: VPO/VPT → Control B or F only.
        self.assertHasIssue("BEVA110M-AHFHZ-VPO", "Options")

    def test_vpo_blocks_rei(self) -> None:
        self.assertHasIssue("BEVA110M-ABFHC-VPO-REI", "Options")

    def test_csv_constant_volume_valid(self) -> None:
        # CSV + Construction A + Bodies 1 + Size 10 + Pressure M + Design A
        # + Control C + Controller N + Orientation H + Failsafe Z → fully valid.
        ok, _, _, _, issues, _, _ = _decode("CSVA110M-ACNHZ")
        self.assertTrue(ok)
        self.assertEqual(issues, [])


class CelerisIIRulesTests(ValidationTestCase):
    """Celeris II rules per PDS p.12 (MKT-0006 Rev F) — Phase A cleanup."""

    def test_construction_c_now_valid(self) -> None:
        # Construction C was missing from the prior code; PDS p.12 documents it.
        ok, _, _, _, issues, _, _ = _decode("MAVC108M-AMEHZ")
        self.assertTrue(ok)
        const_issues = [i for i in issues if i["field"] == "Construction"]
        self.assertEqual(const_issues, [])

    def test_construction_d_requires_single_body(self) -> None:
        self.assertHasIssue("MAVD208M-AMEHZ", "Bodies")

    def test_construction_d_blocks_sfb(self) -> None:
        self.assertHasIssue("MAVD108M-AMEHZ-SFB", "Options")

    def test_construction_d_blocks_size_14(self) -> None:
        self.assertHasIssue("MAVD114M-AMEHZ", "Size")

    def test_bodies_3_or_4_invalid(self) -> None:
        # PDS p.12 lists F/1/2 only — no triple/quad on Celeris II.
        self.assertHasIssue("MAVA308M-AMEHZ", "Bodies")
        self.assertHasIssue("MAVA408M-AMEHZ", "Bodies")

    def test_bodies_2_size_08_invalid(self) -> None:
        # Bodies = 2 documented as 10/12/14 only.
        self.assertHasIssue("MAVA208M-AMEHZ", "Bodies")

    def test_pressure_l_invalid(self) -> None:
        # PDS p.12: Celeris II is Medium pressure only.
        self.assertHasIssue("MAVA108L-AMEHZ", "Pressure")

    def test_design_s_invalid(self) -> None:
        # PDS p.12: Celeris II Design = A only (conical).
        self.assertHasIssue("MAVA108M-SMEHZ", "Valve Design")

    def test_invalid_options_rejected(self) -> None:
        # The phantom options B/F/M/P/O/R/T were removed in the cleanup.
        self.assertHasIssue("MAVA108M-AMEHZ-P", "Options")
        self.assertHasIssue("MAVA108M-AMEHZ-O", "Options")
        self.assertHasIssue("MAVA108M-AMEHZ-T", "Options")

    def test_documented_options_accepted(self) -> None:
        for opt in ("EVI", "FHA", "IBO", "LCL", "PSL", "REI", "SFB", "SFX", "SSB"):
            ok, _, _, _, issues, _, _ = _decode(f"EXVA108M-AMEHZ-{opt}")
            self.assertTrue(ok)
            opt_issues = [i for i in issues if i["field"] == "Options"]
            self.assertEqual(opt_issues, [], f"Option {opt} should be accepted; got {opt_issues}")

    def test_controller_h_on_supply_invalid(self) -> None:
        # Hood controller (H) is exhaust-only.
        self.assertHasIssue("MAVA108M-AMHHZ", "Controller")

    def test_hood_with_low_speed_actuator_invalid(self) -> None:
        # Note 2: Hood valves cannot have low-speed actuators (H, I, L).
        self.assertHasIssue("EXVA108M-AHHHZ", "Control Type")
        self.assertHasIssue("EXVA108M-AIHHZ", "Control Type")
        self.assertHasIssue("EXVA108M-ALHHZ", "Control Type")

    def test_reo_requires_pneumatic(self) -> None:
        # Note 4: REO is for pneumatic actuators only.
        self.assertHasIssue("EXVA108M-AMEHZ-REO", "Options")

    def test_reo_requires_horizontal(self) -> None:
        self.assertHasIssue("EXVA108M-ANEUZ-REO", "Options")

    def test_reo_pneumatic_horizontal_valid(self) -> None:
        ok, _, _, _, issues, _, _ = _decode("EXVA108M-ANEHZ-REO")
        self.assertTrue(ok)
        opt_issues = [i for i in issues if i["field"] == "Options"]
        self.assertEqual(opt_issues, [])

    def test_wre_requires_ip_rated_actuator(self) -> None:
        # Note 5: WRE → Control I, L, or M.
        self.assertHasIssue("EXVA108M-AHEHZ-WRE", "Options")
        self.assertHasIssue("EXVA108M-ANEHZ-WRE", "Options")

    def test_wre_requires_horizontal(self) -> None:
        self.assertHasIssue("EXVA108M-AMEUZ-WRE", "Options")

    def test_ssb_requires_construction_a(self) -> None:
        self.assertHasIssue("MAVB108M-AMEHZ-SSB", "Options")


class ExistingRulesRegressionTests(ValidationTestCase):
    """Spot-checks of pre-existing rules to guard against accidental regressions."""

    def test_cscp_controller_b_requires_bmt_protocol(self) -> None:
        self.assertHasIssue("PVEA110M-AMBHY", "Communication Protocol")

    def test_base_upgradeable_t_requires_controller_n(self) -> None:
        self.assertHasIssue("BEVA110M-ATFCZ", "Valve Controller Designation")

    def test_cscp_stainless_blocks_sfb(self) -> None:
        # Construction E/F (stainless) excludes SFB/SFD/SFI/SSB per p.1 stainless page.
        self.assertHasIssue("PVEE110M-AMBHY-BMT-SFB", "Options")

    def test_cscp_stainless_blocks_ssb(self) -> None:
        self.assertHasIssue("PVEF112M-AMBHY-BMT-SSB", "Options")

    def test_cscp_stainless_with_allowed_options_valid(self) -> None:
        # PSL and REI are still allowed on stainless.
        ok, _, _, _, issues, _, _ = _decode("PVEE110M-AMBHY-BMT-PSL-REI")
        self.assertTrue(ok)
        opt_issues = [i for i in issues if i["field"] == "Options"]
        self.assertEqual(opt_issues, [])


class StructuralWarningsTests(ValidationTestCase):
    """parse_model now emits structured warnings keyed by logical field; the
    process_model_structured wrapper must route them to the right product-aware
    display label without string-matching the message text."""

    def test_empty_model_fails_to_parse(self) -> None:
        ok, msg, *_ = _decode("")
        self.assertFalse(ok)
        self.assertIn("empty", msg.lower())

    def test_short_base_produces_base_issue(self) -> None:
        # 7-char base → routed to product-aware "Base" label
        self.assertHasIssue("MAVA10M-AMEHZ", "Base")

    def test_short_suffix_produces_suffix_issue(self) -> None:
        self.assertHasIssue("MAVA108M-AMEH", "Suffix")

    def test_unknown_prefix_routes_to_family_label(self) -> None:
        # Unknown prefix → use the fallback "Valve Family" label.
        self.assertHasIssue("ZZZA108M-AMEHZ", "Valve Family")


class TherisNoteFilteringTests(ValidationTestCase):
    """Note 2 (14" + M + L) should only show on the matching configuration."""

    def test_note_2_appears_only_on_violating_config(self) -> None:
        _, _, _, notes, _, _, _ = _decode("HSVA114M-LIAHZ")
        self.assertTrue(any("14-inch valves are currently NOT available" in n for n in notes),
                        "Note 2 should appear on 14M+L config")

    def test_note_2_hidden_on_14in_medium_standard(self) -> None:
        _, _, _, notes, _, _, _ = _decode("HSVA114M-SIAHZ")
        self.assertFalse(any("14-inch valves are currently NOT available" in n for n in notes),
                         "Note 2 should not appear on 14M+S config")

    def test_note_2_hidden_on_14in_low_pressure(self) -> None:
        # A different rule (L+L) will fire here, but note 2 (M+L specific) shouldn't.
        _, _, _, notes, _, _, _ = _decode("HSVA114L-AIAHZ")
        self.assertFalse(any("14-inch valves are currently NOT available" in n for n in notes),
                         "Note 2 should not appear on 14L config")


if __name__ == "__main__":
    unittest.main()
