"""Route registration and registry response tests; no archive calls."""
import unittest
from fastapi.testclient import TestClient
from main import app

class ValidationAPIContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.client=TestClient(app)
    def test_required_endpoints_registered(self):
        routes={(r.path,method.lower()) for r in app.routes for method in (getattr(r,"methods",None) or set())}
        expected={("/api/validation/targets","get"),("/api/validation/targets/{target_id}","get"),("/api/validation/run/{target_id}","post"),
            ("/api/validation/results/{target_id}","get"),("/api/validation/lightcurve/{target_id}","get"),("/api/validation/motion/{target_id}","get"),("/api/validation/evidence/{target_id}","get")}
        self.assertTrue(expected.issubset(routes),expected-routes)
    def test_registry_returns_five_complete_reference_records(self):
        result=self.client.get("/api/validation/targets"); self.assertEqual(result.status_code,200); body=result.json(); self.assertEqual(body["count"],5)
        for target in body["targets"]:
            ref=target["reference"]; self.assertEqual(ref["frame"],"ICRS"); self.assertTrue(ref["provenance"]); self.assertTrue(ref["reference_url"])
    def test_unknown_target_is_404(self): self.assertEqual(self.client.get("/api/validation/targets/not-a-target").status_code,404)
    def test_wise_run_and_evidence_routes_return_structured_real_data(self):
        run=self.client.post("/api/validation/run/wise_0855?live_archive_query=false&use_discovery_cache=false")
        self.assertEqual(run.status_code,200,run.text); self.assertEqual(run.json()["validation_status"],"INCONCLUSIVE")
        for path in ("/api/validation/results/wise_0855","/api/validation/lightcurve/wise_0855","/api/validation/motion/wise_0855","/api/validation/evidence/wise_0855"):
            response=self.client.get(path); self.assertEqual(response.status_code,200,path)
        for path in ("/api/validation/astrometry/wise_0855/plot","/api/validation/photometry/wise_0855/plot","/api/validation/difference/wise_0855","/api/validation/image/wise_0855/first"):
            response=self.client.get(path); self.assertEqual(response.status_code,200,path); self.assertEqual(response.headers["content-type"],"image/png")

if __name__=="__main__": unittest.main(verbosity=2)
