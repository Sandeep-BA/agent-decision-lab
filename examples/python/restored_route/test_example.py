# Author: Sandeep Belgavi. Original behavioral boundary tests.
import unittest,json
from example import *

class Behavior(unittest.TestCase):
    def required(self):return {"route":"a","revision":3,"endpoint":"https://gateway.invalid/model/"}
    def test_missing_route_creates_no_request(self):
        calls=[];decision=resume_route(self.required(),None)
        if decision=="ready-for-credential-resolution":calls.append("request")
        self.assertEqual(calls,[]);self.assertEqual(decision,"blocked-missing-route")
    def test_same_route(self):self.assertEqual(resume_route(self.required(),self.required()),"ready-for-credential-resolution")
    def test_changed_host_path_revision(self):
        for key,value in [("endpoint","https://other.invalid/model/"),("endpoint","https://gateway.invalid/other/"),("revision",4)]:
            current=self.required();current[key]=value;self.assertTrue(resume_route(self.required(),current).startswith("blocked-"))
    def test_no_embedded_credentials_or_query(self):
        for endpoint in ("https://user:secret@gateway.invalid/","https://gateway.invalid/?x=1","http://gateway.invalid/","https://gateway.invalid:0/"):
            with self.assertRaises(ValueError):endpoint_identity(endpoint)
    def test_case_and_default_port(self):self.assertEqual(endpoint_identity("https://GATEWAY.invalid:443/model/"),endpoint_identity("https://gateway.invalid/model/"))
    def test_invalid_contract(self):self.assertEqual(resume_route(self.required(),[]),"blocked-invalid-contract")

if __name__ == "__main__":unittest.main()
