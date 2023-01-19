import unittest

from backend.security import generate_salt_hash, get_hash

class Test_Security(unittest.TestCase):
	def test_hash(self):
		for test_case in ('test', ''):
			result = generate_salt_hash(test_case)
			self.assertEqual(result[1], get_hash(result[0], test_case))
		