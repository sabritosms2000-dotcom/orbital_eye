"""Synthetic tests; no real FITS pixels or source detections are used."""
import unittest
from validation.astrometry import compare_epochs

class SyntheticValidationTests(unittest.TestCase):
    def test_synthetic_centroid_motion_is_separate_from_prediction(self):
        def row(mjd,ra): return {"mjd":mjd,"predicted":{"ra_deg":ra,"dec_deg":0},"measured_centroid":{"ra_deg":ra,"dec_deg":0,"uncertainty_arcsec":.1}}
        out=compare_epochs(row(60000,10),row(60365.25,10+1/3600))
        self.assertAlmostEqual(out["predicted_angular_shift_arcsec"],1,places=3)
        self.assertAlmostEqual(out["measured_angular_shift_arcsec"],1,places=3)
    def test_no_measured_centroids_means_no_measured_motion(self):
        a={"mjd":60000,"predicted":{"ra_deg":10,"dec_deg":0},"measured_centroid":None}
        b={"mjd":60365.25,"predicted":{"ra_deg":10.1,"dec_deg":0},"measured_centroid":None}
        self.assertIsNone(compare_epochs(a,b)["measured_angular_shift_arcsec"])

if __name__=="__main__": unittest.main(verbosity=2)
