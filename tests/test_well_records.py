import tempfile,unittest
from pathlib import Path
from well.ledger import WellLedger
from well.records import WellService
class T(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.s=WellService(WellLedger(Path(self.tmp.name)/"t.db"))
 def tearDown(self):self.tmp.cleanup()
 def test_provenance_retrieval(self):
  e=self.s.add_observation(owner_id="alice",source_ref="note:1",text="red kite",evidence_status="observed");h=self.s.search(owner_id="alice",query="red kite")
  self.assertEqual(h[0]["event"]["event_id"],e["event_id"]);self.assertEqual(h[0]["event"]["payload"]["source_ref"],"note:1")
 def test_owner_boundary(self):
  e=self.s.add_observation(owner_id="alice",source_ref="a",text="fact")
  with self.assertRaises(ValueError):self.s.propose_pattern(owner_id="bob",title="x",summary="y",supporting_event_ids=[e["event_id"]],derivation="manual",confidence=.5)
 def test_pattern_evidence(self):
  e=self.s.add_observation(owner_id="a",source_ref="a",text="fact");p=self.s.propose_pattern(owner_id="a",title="pattern",summary="maybe",supporting_event_ids=[e["event_id"]],derivation="review",confidence=.4,counterexamples=["exception"])
  self.assertEqual(p["payload"]["confidence"],.4);self.assertEqual(p["payload"]["counterexamples"],["exception"])
 def test_bad_status(self):
  with self.assertRaises(ValueError):self.s.add_observation(owner_id="a",source_ref="a",text="x",evidence_status="certain")
if __name__=="__main__":unittest.main()
