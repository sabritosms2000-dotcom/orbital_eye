"""Local FITS integration tests for Phase 5 (no live archive calls)."""
import unittest
from validation.engine import validate_all_targets, validate_target
from validation.target_registry import list_targets

class Phase5IntegrationTests(unittest.TestCase):
    def test_registry_has_five_sources_and_unknown_kinematics_are_null(self):
        targets=list_targets(); self.assertEqual(len(targets),5)
        self.assertTrue(all(t["reference"].get("reference_url") and t["reference"].get("provenance") for t in targets))
        rw=next(t for t in targets if t["id"]=="rw_aurigae")["reference"]
        self.assertIsNone(rw["parallax_mas"])

    def test_target_with_local_observations_runs_validation(self):
        # All 5 targets now have local FITS; validation runs but may be INCONCLUSIVE
        r=validate_target("barnards_star",False,False)
        self.assertIn(r["validation_status"], {"INCONCLUSIVE", "PARTIALLY_VALIDATED", "VALIDATED", "FAILED_VALIDATION"})
        self.assertFalse(r["is_confirmed_detection"])
        self.assertGreater(len(r["epochs"]), 0)

    def test_wise0855_audit_separates_prediction_and_measured_motion(self):
        r=validate_target("wise_0855",False,False)
        self.assertEqual(r["validation_status"],"INCONCLUSIVE")
        self.assertGreaterEqual(len(r["epochs"]),2)  # Now has 3 epochs (2 original + 1 new D3)
        # Successful D3 epochs should have SNR > 5 and centroid candidates
        success_epochs = [e for e in r["epochs"] if e.get("status") == "success"]
        d3_success = [e for e in success_epochs if e.get("band") == "SPHEREx-D3" and e.get("photometry",{}).get("snr",0) > 5]
        self.assertGreaterEqual(len(d3_success), 2)  # At least the two original cutouts
        # measured_centroid may be missing or None; centroid_candidate should exist for successful epochs
        self.assertTrue(all(e.get("measured_centroid") is None for e in success_epochs))
        self.assertTrue(all(e.get("centroid_candidate") is not None for e in success_epochs))
        self.assertIsNone(r["epoch_comparison"]["measured_angular_shift_arcsec"])
        self.assertFalse(r["is_confirmed_detection"])
        self.assertEqual(r["image_comparison"]["status"],"wcs_aligned")

    def test_all_five_have_evidence_based_statuses(self):
        data=validate_all_targets(False,False)
        self.assertEqual(data["count"],5)
        self.assertTrue(all(x["validation_status"] in {"VALIDATED","PARTIALLY_VALIDATED","INSUFFICIENT_DATA","INCONCLUSIVE","FAILED_VALIDATION"} for x in data["results"]))

if __name__=="__main__": unittest.main(verbosity=2)
