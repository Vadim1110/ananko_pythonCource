import unittest
from unittest.mock import patch
import sqlite3
from api import BankAPI

class TestBankAPI(unittest.TestCase):

    @classmethod
    def _initialize_test_db(cls):
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()

        cursor.execute('CREATE TABLE Bank (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE)')
        cursor.execute('''
                CREATE TABLE User (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    surname TEXT NOT NULL,
                    birth_day TEXT,
                    Accounts TEXT NOT NULL
                )
            ''')
        cursor.execute('''
                CREATE TABLE Account (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    type TEXT NOT NULL CHECK(type IN ('credit', 'debit')),
                    account_number TEXT NOT NULL UNIQUE,
                    bank_id INTEGER NOT NULL,
                    currency TEXT NOT NULL,
                    amount REAL NOT NULL,
                    discount INTEGER CHECK(discount IN (25, 30, 50)),
                    status TEXT CHECK(status IN ('gold', 'silver', 'platinum')),
                    FOREIGN KEY (user_id) REFERENCES User(id),
                    FOREIGN KEY (bank_id) REFERENCES Bank(id)
                )
            ''')
        cursor.execute('''
                CREATE TABLE "Transaction" (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bank_sender_name TEXT NOT NULL,
                    account_sender_id INTEGER NOT NULL,
                    bank_receiver_name TEXT NOT NULL,
                    account_receiver_id INTEGER NOT NULL,
                    sent_currency TEXT NOT NULL,
                    sent_amount REAL NOT NULL,
                    datetime TEXT
                )
            ''')

        cursor.execute("INSERT INTO Bank (name) VALUES ('Bank A')")
        cursor.execute("INSERT INTO Bank (name) VALUES ('Bank B')")

        cursor.execute('''
                INSERT INTO User (name, surname, birth_day, Accounts) 
                VALUES ('John', 'Doe', '1980-01-01', '1,2')
            ''')
        cursor.execute('''
                INSERT INTO User (name, surname, birth_day, Accounts) 
                VALUES ('Jane', 'Smith', '1990-05-15', '3')
            ''')
        cursor.execute('''
                INSERT INTO User (name, surname, birth_day, Accounts) 
                VALUES ('Charlie', 'Brown', '1975-03-10', '4')
            ''')

        cursor.execute('''
                INSERT INTO Account (user_id, type, account_number, bank_id, currency, amount, status)
                VALUES (1, 'debit', 'ID-USD-1001000001-', 1, 'USD', 5000.00, 'gold')
            ''')
        cursor.execute('''
                INSERT INTO Account (user_id, type, account_number, bank_id, currency, amount, status)
                VALUES (2, 'debit', 'ID-EUR-2001000003-', 2, 'EUR', 3000.00, 'platinum')
            ''')
        cursor.execute('''
                INSERT INTO Account (user_id, type, account_number, bank_id, currency, amount, status)
                VALUES (3, 'credit', 'ID-USD-1003000004-', 1, 'USD', -500.00, 'silver')
            ''')

        conn.commit()
        conn.close()

    def setUp(self):
        self.api = BankAPI()

    def test_get_bank_name(self):
        actual = self.api.get_bank_name(1)
        expected = 'Bank A'
        self.assertEqual(actual, expected)

        actual = self.api.get_bank_name(999)
        expected = None
        self.assertEqual(actual, expected)

    @patch('api.BankAPI._get_exchange_rates')
    def test_transfer_money(self, mock_rates):
        mock_rates.return_value = {'USD': 1.0, 'EUR': 0.85}

        transfer_data = {
            'sender_account_id': 1,
            'receiver_account_id': 2,
            'amount': 100.0,
            'currency': 'USD'
        }
        actual = self.api.transfer_money(transfer_data)
        expected_status = 'success'
        self.assertEqual(actual['status'], expected_status)


        transfer_data['amount'] = 10000.0
        actual = self.api.transfer_money(transfer_data)
        expected_message = 'Insufficient funds'
        self.assertEqual(actual['status'], 'error')
        self.assertIn(expected_message, actual['message'])

        transfer_data['sender_account_id'] = 999
        actual = self.api.transfer_money(transfer_data)
        expected_message = 'not found'
        self.assertEqual(actual['status'], 'error')
        self.assertIn(expected_message, actual['message'])

    def test_add_banks(self):
        expected_status = 'success'

        banks = [{'name': 'Bank A'}, {'name': 'Bank B'}]
        actual = self.api.add_banks(banks)
        self.assertEqual(actual['status'], expected_status)

        actual = self.api.add_banks({'name': 'Test Bank 1'})
        expected_status = 'success'
        self.assertEqual(actual['status'], expected_status)

    def test_add_users(self):
        actual = self.api.add_users({'user_full_name': 'Alice Johnson'})
        expected_status = 'success'
        self.assertEqual(actual['status'], expected_status)

        users = [
            {'user_full_name': 'Bob Smith', 'birth_day': '1995-05-05'},
            {'user_full_name': 'Vadim Vadimovich'}
        ]
        actual = self.api.add_users(users)
        self.assertEqual(actual['status'], expected_status)

        actual = self.api.add_users({'user_full_name': ''})
        expected_status = 'success'
        self.assertEqual(actual['status'], expected_status)
        expected_data_length = 0
        self.assertEqual(len(actual['data']), expected_data_length)

    def test_add_accounts(self):
        account = {
            'user_id': 1,
            'type': 'debit',
            'account_number': 'ID-USD-1003000004-',
            'bank_id': 1,
            'currency': 'USD',
            'amount': 2000.00
        }
        actual = self.api.add_accounts(account)
        expected_status = 'success'
        self.assertEqual(actual['status'], expected_status)

        accounts = [
            {
                'user_id': 2,
                'type': 'credit',
                'account_number': 'ID-EUR-2002000005-',
                'bank_id': 2,
                'currency': 'EUR',
                'amount': -500.00,
                'status': 'silver'
            },
            {
                'user_id': 1,
                'type': 'debit',
                'account_number': 'ID-USD-1004000006-',
                'bank_id': 1,
                'currency': 'USD',
                'amount': 3000.00,
                'status': 'gold'
            }
        ]
        actual = self.api.add_accounts(accounts)
        self.assertEqual(actual['status'], expected_status)

        account['account_number'] = 'ID-EUR-2002000005-'
        actual = self.api.add_accounts(account)
        expected_status = 'success'
        self.assertEqual(actual['status'], expected_status)

    def test_get_account(self):
        actual = self.api.get_account(1)
        expected_id = 1
        expected_user_id = 1
        expected_type = 'debit'
        self.assertEqual(actual['id'], expected_id)
        self.assertEqual(actual['user_id'], expected_user_id)
        self.assertEqual(actual['type'], expected_type)

        actual = self.api.get_account(999)
        expected = None
        self.assertEqual(actual, expected)

    def test_get_transactions(self):
        actual = self.api.get_transactions(1)
        expected_sender_id = 1
        expected_amount = 100.0
        self.assertEqual(actual[0]['account_sender_id'], expected_sender_id)
        self.assertEqual(actual[0]['sent_amount'], expected_amount)

    def test_get_transactions(self):

        start_date = '2023-01-01'
        end_date = '2023-01-02'
        actual = self.api.get_transactions(1, start_date, end_date)
        expected_count = 6
        self.assertEqual(len(actual), expected_count)

    def test_get_transactions(self):

        actual = self.api.get_transactions(3)
        expected_count = 0
        self.assertEqual(len(actual), expected_count)

    @patch('api.BankAPI._get_exchange_rates')
    def test_get_bank_with_largest_capital(self, mock_rates):
        mock_rates.return_value = {'USD': 1.0, 'EUR': 0.85}

        actual = self.api.get_bank_with_largest_capital()
        expected_status = 'success'
        expected_bank_id = 1
        assert actual['status'] == expected_status
        assert actual['data']['bank_id'] == expected_bank_id

    def test_get_bank_with_oldest_client(self):
        actual = self.api.get_bank_with_oldest_client()
        expected_bank_id = 2
        expected_bank_name = 'Bank B'
        assert actual['id'] == expected_bank_id
        assert actual['name'] == expected_bank_name

    def test_get_bank_with_most_active_users(self):
        actual = self.api.get_bank_with_most_active_users()
        expected_status = 'success'
        expected_bank_id = 1
        assert actual['status'] == expected_status
        assert actual['data']['bank_id'] == expected_bank_id

    @patch('random.choices')
    def test_apply_random_discounts(self, mock_choices):
        mock_choices.return_value = [25, 30]

        actual = self.api.apply_random_discounts(max_users=2)
        expected_status = 'success'
        expected_data_length = 1
        assert actual['status'] == expected_status
        assert len(actual['data']) == expected_data_length

    def test_get_users_with_debts(self):
        actual = self.api.get_users_with_debts()


        expected_count = 1
        expected_name = 'Vadim'
        expected_surname = 'Vadimovich'

        self.assertEqual(len(actual), expected_count)
        self.assertEqual(actual[0]['name'], expected_name)
        self.assertEqual(actual[0]['surname'], expected_surname)

if __name__ == '__main__':
    unittest.main()