import unittest
from personas.registry import get_persona,render_persona_context
class T(unittest.TestCase):
 def test_registry(self):self.assertEqual(get_persona("Orochimaru").key,"orochimaru")
 def test_unknown(self):
  with self.assertRaises(ValueError):get_persona("unknown")
 def test_no_authority(self):
  s=render_persona_context(get_persona("orochimaru"));self.assertIn("Do not grant access",s);self.assertIn("untrusted evidence",s)
if __name__=="__main__":unittest.main()
