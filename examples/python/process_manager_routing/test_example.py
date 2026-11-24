"""Author: Sandeep Belgavi. Transition authority and race tests."""
import unittest
from example import State,handle,demo
class Tests(unittest.TestCase):
 def msg(self,**kw):return dict(kind='assessment',revision=4,digest='D1',request='A17',classification='accept',**kw)
 def test_late(self):self.assertEqual(demo()['commands'],['open_review'])
 def test_assessment_first(self):
  s,c,r=handle(State(),self.msg());self.assertEqual(s.phase,'accepted');self.assertEqual(handle(s,{'kind':'timeout','revision':4})[1],[])
 def test_duplicate(self):
  m=self.msg();s,c,_=handle(State(),m);self.assertEqual(handle(s,m)[1],[])
 def test_bad_digest(self):
  m=self.msg();m['digest']='D2';self.assertEqual(handle(State(),m)[2],'wrong_input')
 def test_bad_request(self):
  m=self.msg();m['request']='A18';self.assertEqual(handle(State(),m)[2],'wrong_input')
 def test_unknown_choice(self):
  m=self.msg();m['classification']='execute_shell';self.assertEqual(handle(State(),m)[0].phase,'awaiting_review')
 def test_unknown_type(self):self.assertEqual(handle(State(),{'kind':'noise','revision':4})[2],'unsupported_message')
if __name__=='__main__':unittest.main()
