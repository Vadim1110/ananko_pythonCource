import unittest
from ananko_pythonCource.lab_6.api import BankAPI  # api.py должен лежать в корне рядом с tests

class TestBankAPI(unittest.TestCase):
    def setUp(self):
        self.bank_api = BankAPI()

    def test_example(self):
        # Твой тест здесь
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
