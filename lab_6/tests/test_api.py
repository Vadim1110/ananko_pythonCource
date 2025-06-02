import unittest
from ananko_pythonCource.lab_6.api import BankAPI

class TestBankAPI(unittest.TestCase):
    def setUp(self):
        self.bank_api = BankAPI()

    def test_example(self):
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
