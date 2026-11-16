import unittest
from fastapi.testclient import TestClient
from api.app import app
class T(unittest.TestCase):
 def setUp(self):self.a=app.state.authenticator;self.m=app.state.model_adapter;app.state.authenticator=None;app.state.model_adapter=None;self.c=TestClient(app)
 def tearDown(self):app.state.authenticator=self.a;app.state.model_adapter=self.m
 def test_private_route_denies(self):self.assertEqual(self.c.get("/search?q=x").status_code,401)
 def test_chat_requires_auth(self):self.assertEqual(self.c.post("/chat",json={"message":"hi","consent":True}).status_code,401)
 def test_personas(self):self.assertIn("orochimaru",[x["key"] for x in self.c.get("/personas").json()])
 def test_no_model_fails_closed(self):
  app.state.authenticator=lambda token:{"sub":"alice"};r=self.c.post("/chat",headers={"Authorization":"Bearer synthetic"},json={"message":"hi","consent":True});self.assertEqual(r.status_code,503)
if __name__=="__main__":unittest.main()
