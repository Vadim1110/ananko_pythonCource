import sqlite3 as db
from typing import List, Dict, Union, Optional, Any
import csv
import requests
from datetime import datetime, timedelta
from functools import wraps
import logging
from models import DatabaseConnection, BankSystem
from validations import (
    validate_user_full_name,
    validate_account_number,
    validate_enum_field,
    get_current_datetime
)
import random


logger = logging.getLogger(__name__)

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """Validate that all required fields are present in the data."""
    missing = [field for field in required_fields if field not in data]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

def db_connection(func):
    """Decorator to handle database connections."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        with DatabaseConnection() as cursor:
            kwargs['cursor'] = cursor
            try:
                result = func(*args, **kwargs)
                return result
            except ValueError as e:
                logger.warning(f"Validation error in {func.__name__}: {str(e)}")
                return {'status': 'error', 'message': str(e)}
            except db.IntegrityError as e:
                logger.warning(f"Integrity error in {func.__name__}: {str(e)}")
                return {'status': 'error', 'message': 'Database integrity error'}
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
                return {'status': 'error', 'message': 'Internal server error'}
    return wrapper

class BankAPI(BankSystem):
    """API for bank system operations."""


    def _get_exchange_rates(self, base_currency: str) -> Dict[str, float]:
        """Get current exchange rates from the currency API.
        """
        try:
            response = requests.get(
                self.exchange_base_url,
                params={
                    'apikey': self.exchange_api_key,
                    'base_currency': base_currency
                },
                timeout=5
            )
            response.raise_for_status()
            return response.json().get('data', {base_currency: 1.0})
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get exchange rates: {str(e)}")
            return {base_currency: 1.0}  # Fallback to 1:1 if API fails

    @db_connection
    def get_bank_name(self, bank_id: int, cursor=None) -> Optional[str]:
        """Get bank name by ID."""
        cursor.execute("SELECT name FROM Bank WHERE id = ?", (bank_id,))
        result = cursor.fetchone()
        return result[0] if result else None

    @db_connection
    def transfer_money(self, sender_account_id: int, receiver_account_id: int,
                       amount: float, currency: str, cursor=None) -> Dict:
        """Perform money transfer between accounts with currency conversion."""
        try:
            # Get full account details including bank names
            cursor.execute('''
                   SELECT a.*, b.name as bank_name 
                   FROM Account a
                   JOIN Bank b ON a.bank_id = b.id
                   WHERE a.id = ?
               ''', (sender_account_id,))
            sender = cursor.fetchone()

            cursor.execute('''
                   SELECT a.*, b.name as bank_name 
                   FROM Account a
                   JOIN Bank b ON a.bank_id = b.id
                   WHERE a.id = ?
               ''', (receiver_account_id,))
            receiver = cursor.fetchone()

            if not sender or not receiver:
                return {'status': 'error', 'message': 'Account(s) not found'}

            # Check sender balance
            if sender['amount'] < amount:
                return {'status': 'error', 'message': 'Insufficient funds'}

            # Get exchange rates
            rates = self._get_exchange_rates(sender['currency'])
            if currency not in rates or receiver['currency'] not in rates:
                return {'status': 'error', 'message': 'Unsupported currency'}

            # Convert amounts
            amount_in_sender_currency = amount / rates[currency] * rates[sender['currency']]
            amount_in_receiver_currency = amount / rates[currency] * rates[receiver['currency']]

            # Update balances
            cursor.execute(
                "UPDATE Account SET amount = ? WHERE id = ?",
                (sender['amount'] - amount_in_sender_currency, sender_account_id)
            )
            cursor.execute(
                "UPDATE Account SET amount = ? WHERE id = ?",
                (receiver['amount'] + amount_in_receiver_currency, receiver_account_id)
            )

            # Record transaction
            cursor.execute(
                '''INSERT INTO "Transaction" (
                    bank_sender_name, account_sender_id, 
                    bank_receiver_name, account_receiver_id,
                    sent_currency, sent_amount, datetime
                ) VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (
                    sender['bank_name'],
                    sender_account_id,
                    receiver['bank_name'],
                    receiver_account_id,
                    currency,
                    amount,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
            )

            return {
                'status': 'success',
                'message': 'Transfer completed successfully',
                'details': {
                    'sender_new_balance': sender['amount'] - amount_in_sender_currency,
                    'receiver_new_balance': receiver['amount'] + amount_in_receiver_currency,
                    'exchange_rate': rates
                }
            }

        except Exception as e:
            logger.error(f"Transfer failed: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': str(e)}

    @db_connection
    def add_banks(self, banks_data: Union[List[Dict], Dict], cursor=None) -> Dict:
        """Add banks with proper validation."""

        added = []
        for bank in banks_data:
            try:
                validate_required_fields(bank, ['name'])
                cursor.execute(
                    "INSERT INTO Bank (name) VALUES (?)",
                    (bank['name'],))
                added.append({'id': cursor.lastrowid, 'name': bank['name']})
            except Exception as e:
                logger.warning(f"Skipping invalid bank data: {str(e)}")
                continue

        return {
            'status': 'success',
            'message': f"Added {len(added)} banks",
            'data': added
        }

    @db_connection
    def add_users(self, users_data: Union[List[Dict], Dict], cursor=None) -> Dict:
        """Add users with proper validation."""

        added = []
        for user in users_data:
            try:
                validate_required_fields(user, ['user_full_name'])
                name, surname = validate_user_full_name(user['user_full_name'])

                cursor.execute(
                    '''INSERT INTO User (name, surname, birth_day, Accounts)
                    VALUES (?, ?, ?, ?)''',
                    (name, surname, user.get('birth_day'), user.get('Accounts', ''))
                )
                added.append({
                    'id': cursor.lastrowid,
                    'name': name,
                    'surname': surname
                })
            except Exception as e:
                logger.warning(f"Skipping invalid user data: {str(e)}")
                continue

        return {
            'status': 'success',
            'message': f"Added {len(added)} users",
            'data': added
        }

    @db_connection
    def add_accounts(self, accounts_data: Union[List[Dict], Dict], cursor=None) -> Dict:
        """
        Add one or more accounts to the database.

        Args:
            accounts_data: Single account dict or list of account dicts

        Returns:
            Dict with status and message/added data
        """
        if isinstance(accounts_data, dict):
            accounts_data = [accounts_data]  # Convert single dict to list with one item

        added = []
        for account in accounts_data:
            try:
                validate_enum_field(account['type'], 'type', ['credit', 'debit'])
                validate_enum_field(account.get('status', ''), 'status', ['gold', 'silver', 'platinum', ''])

                cleaned_account_number = validate_account_number(account['account_number'])

                cursor.execute(
                    '''INSERT INTO Account (
                        user_id, type, account_number, bank_id,
                        currency, amount, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (
                        account['user_id'],
                        account['type'],
                        cleaned_account_number,
                        account['bank_id'],
                        account['currency'],
                        account['amount'],
                        account.get('status')
                    )
                )
                added.append({
                    'id': cursor.lastrowid,
                    'account_number': cleaned_account_number
                })
            except Exception as e:
                logger.warning(f"Skipping invalid account data: {str(e)}")
                continue

        return {
            'status': 'success',
            'message': f"Added {len(added)} accounts",
            'data': added
        }

    @db_connection
    def add_users_from_csv(self, file_path: str) -> Dict:
        """
        Add users from CSV file.

        Args:
            file_path: Path to CSV file

        Returns:
            Dict with status and message/added data
        """
        try:
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f)
                users = []
                for row in reader:
                    try:
                        name, surname = validate_user_full_name(row['user_full_name'])
                        users.append({
                            'user_full_name': f"{name} {surname}",
                            'birth_day': row.get('birth_day'),
                            'Accounts': row.get('Accounts', '')
                        })
                    except Exception as e:
                        logger.warning(f"Skipping invalid user data: {str(e)}")
                        continue

                return self.add_users(users)
        except Exception as e:
            logger.error(f"Failed to read CSV file: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    @db_connection
    def transfer_money(self, sender_account_id: int, receiver_account_id: int,
                       amount: float, currency: str, cursor=None) -> Dict:
        """
        Perform money transfer between accounts with currency conversion.

        Args:
            sender_account_id: ID of sender account
            receiver_account_id: ID of receiver account
            amount: Amount to transfer
            currency: Currency of transfer

        Returns:
            Dict with status and message
        """
        try:
            # Get sender and receiver accounts
            cursor.execute("SELECT * FROM Account WHERE id = ?", (sender_account_id,))
            sender = cursor.fetchone()
            if not sender:
                return {'status': 'error', 'message': 'Sender account not found'}

            cursor.execute("SELECT * FROM Account WHERE id = ?", (receiver_account_id,))
            receiver = cursor.fetchone()
            if not receiver:
                return {'status': 'error', 'message': 'Receiver account not found'}

            # Check sender balance
            if sender['amount'] < amount:
                return {'status': 'error', 'message': 'Insufficient funds'}

            # Get exchange rates
            rates = self._get_exchange_rates(sender['currency'])
            if currency not in rates or receiver['currency'] not in rates:
                return {'status': 'error', 'message': 'Unsupported currency'}

            # Convert amounts
            amount_in_sender_currency = amount / rates[currency] * rates[sender['currency']]
            amount_in_receiver_currency = amount / rates[currency] * rates[receiver['currency']]

            # Update balances
            new_sender_balance = sender['amount'] - amount_in_sender_currency
            new_receiver_balance = receiver['amount'] + amount_in_receiver_currency

            cursor.execute(
                "UPDATE Account SET amount = ? WHERE id = ?",
                (new_sender_balance, sender_account_id)
            )
            cursor.execute(
                "UPDATE Account SET amount = ? WHERE id = ?",
                (new_receiver_balance, receiver_account_id)
            )

            # Record transaction
            cursor.execute(
                '''INSERT INTO Transaction (
                    bank_sender_name, account_sender_id, 
                    bank_receiver_name, account_receiver_id,
                    sent_currency, sent_amount, datetime
                ) VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (
                    sender['bank_name'], sender_account_id,
                    receiver['bank_name'], receiver_account_id,
                    currency, amount, get_current_datetime()
                )
            )

            return {
                'status': 'success',
                'message': 'Transfer completed successfully'
            }
        except Exception as e:
            logger.error(f"Transfer failed: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    @db_connection
    def get_account(self, account_id: int, cursor=None) -> Optional[Dict]:
        """Safe account retrieval with error handling."""
        cursor.execute('''
            SELECT a.*, b.name as bank_name 
            FROM Account a
            JOIN Bank b ON a.bank_id = b.id
            WHERE a.id = ?
        ''', (account_id,))
        result = cursor.fetchone()
        return dict(result) if result else None

    @db_connection
    def get_transactions(self, account_id: int,
                         start_date: str = None,
                         end_date: str = None,
                         cursor=None) -> List[Dict]:
        """Get transaction history for an account."""
        try:
            query = '''
                SELECT * FROM "Transaction"
                WHERE account_sender_id = ? OR account_receiver_id = ?
            '''
            params = [account_id, account_id]

            if start_date:
                query += " AND datetime >= ?"
                params.append(start_date)
            if end_date:
                query += " AND datetime <= ?"
                params.append(end_date)

            query += " ORDER BY datetime DESC"

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get transactions: {str(e)}")
            return []

    @db_connection
    def transfer_money(self, transfer_data: Dict, cursor=None) -> Dict:
        """Enhanced money transfer with complete validation."""
        try:
            # Validate required fields
            validate_required_fields(transfer_data, [
                'sender_account_id',
                'receiver_account_id',
                'amount',
                'currency'
            ])

            # Get accounts with verification
            sender = self.get_account(transfer_data['sender_account_id'])
            receiver = self.get_account(transfer_data['receiver_account_id'])

            if not sender or not receiver:
                return {'status': 'error', 'message': 'One or both accounts not found'}

            # Check sender balance
            if sender['amount'] < transfer_data['amount']:
                return {'status': 'error', 'message': 'Insufficient funds'}

            # Get exchange rates
            rates = self._get_exchange_rates(sender['currency'])
            if transfer_data['currency'] not in rates or receiver['currency'] not in rates:
                return {'status': 'error', 'message': 'Unsupported currency'}

            # Convert amounts
            amount_in_sender_currency = transfer_data['amount'] / rates[transfer_data['currency']] * rates[
                sender['currency']]
            amount_in_receiver_currency = transfer_data['amount'] / rates[transfer_data['currency']] * rates[
                receiver['currency']]

            # Update balances
            new_sender_balance = sender['amount'] - amount_in_sender_currency
            new_receiver_balance = receiver['amount'] + amount_in_receiver_currency

            cursor.execute(
                "UPDATE Account SET amount = ? WHERE id = ?",
                (new_sender_balance, transfer_data['sender_account_id'])
            )
            cursor.execute(
                "UPDATE Account SET amount = ? WHERE id = ?",
                (new_receiver_balance, transfer_data['receiver_account_id'])
            )

            # Record transaction
            cursor.execute(
                '''INSERT INTO "Transaction" (
                    bank_sender_name, account_sender_id, 
                    bank_receiver_name, account_receiver_id,
                    sent_currency, sent_amount, datetime
                ) VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (
                    sender['bank_name'],
                    transfer_data['sender_account_id'],
                    receiver['bank_name'],
                    transfer_data['receiver_account_id'],
                    transfer_data['currency'],
                    transfer_data['amount'],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
            )

            return {
                'status': 'success',
                'message': 'Transfer completed successfully',
                'details': {
                    'sender_new_balance': new_sender_balance,
                    'receiver_new_balance': new_receiver_balance,
                    'exchange_rate': rates
                }
            }

        except Exception as e:
            logger.error(f"Transfer failed: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': str(e)}

    @db_connection
    def apply_random_discounts(self, max_users: int = 10, cursor=None) -> Dict:
        """Apply random discounts to users' credit accounts (25%, 30%, or 50%)."""
        try:
            # Get random users with credit accounts
            cursor.execute('''
                SELECT DISTINCT u.id 
                FROM User u
                JOIN Account a ON u.id = a.user_id
                WHERE a.type = 'credit'
                ORDER BY RANDOM()
                LIMIT ?
            ''', (max_users,))

            user_ids = [row[0] for row in cursor.fetchall()]
            discounts = random.choices([25, 30, 50], k=len(user_ids))

            results = []
            for user_id, discount in zip(user_ids, discounts):
                cursor.execute('''
                    UPDATE Account 
                    SET discount = ?
                    WHERE user_id = ? AND type = 'credit'
                ''', (discount, user_id))
                results.append({'user_id': user_id, 'discount': f"{discount}%"})

            return {
                'status': 'success',
                'message': f'Applied discounts to {len(results)} credit accounts',
                'data': results
            }
        except Exception as e:
            logger.error(f"Failed to apply discounts: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': str(e)}

    @db_connection
    def get_users_with_debts(self, cursor=None) -> List[Dict]:
        """Get full names of users with negative account balances."""
        cursor.execute('''
            SELECT DISTINCT u.id, u.name, u.surname 
            FROM User u
            JOIN Account a ON u.id = a.user_id
            WHERE a.amount < 0
        ''')
        return [dict(row) for row in cursor.fetchall()]

    @db_connection
    def get_bank_with_largest_capital(self, cursor=None) -> Dict:
        """Get bank with the highest total capital in its native currency."""
        try:
            # Get all exchange rates once
            rates = self._get_exchange_rates('USD')  # Base is USD

            # First get all banks with their accounts
            cursor.execute('''
                SELECT b.id, b.name, a.currency, SUM(a.amount) as total
                FROM Bank b
                JOIN Account a ON b.id = a.bank_id
                GROUP BY b.id, a.currency
            ''')

            bank_totals = {}
            for row in cursor.fetchall():
                bank_id, bank_name, currency, amount = row
                if bank_id not in bank_totals:
                    bank_totals[bank_id] = {'name': bank_name, 'total_usd': 0}

                # Convert to USD equivalent
                if currency == 'USD':
                    bank_totals[bank_id]['total_usd'] = amount
                else:
                    bank_totals[bank_id]['total_usd'] = amount / rates.get(currency, 1.0)

            if not bank_totals:
                return {'status': 'error', 'message': 'No banks found'}

            # Find bank with largest capital
            max_bank = max(bank_totals.items(), key=lambda x: x[1]['total_usd'])

            return {
                'status': 'success',
                'data': {
                    'bank_id': max_bank[0],
                    'bank_name': max_bank[1]['name'],
                    'total_capital_usd': max_bank[1]['total_usd'],
                    'message': 'All amounts converted to USD for comparison'
                }
            }

        except Exception as e:
            logger.error(f"Failed to calculate bank capital: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    @db_connection
    def get_bank_with_oldest_client(self, cursor=None) -> Dict:
        """Get bank serving the oldest client by birth date."""
        cursor.execute('''
            SELECT b.id, b.name, MIN(u.birth_day) as oldest_birthday
            FROM Bank b
            JOIN Account a ON b.id = a.bank_id
            JOIN User u ON a.user_id = u.id
            GROUP BY b.id
            ORDER BY oldest_birthday
            LIMIT 1
        ''')
        return dict(cursor.fetchone())

    @db_connection
    def get_bank_with_most_active_users(self, cursor=None) -> Dict:
        """Get bank with most unique users performing outbound transactions."""
        try:
            cursor.execute('''
                SELECT 
                    b.id,
                    b.name,
                    COUNT(DISTINCT a.user_id) as active_users
                FROM "Transaction" t
                JOIN Account a ON t.account_sender_id = a.id
                JOIN Bank b ON a.bank_id = b.id
                GROUP BY b.id
                ORDER BY active_users DESC
                LIMIT 1
            ''')

            result = cursor.fetchone()
            if not result:
                return {
                    'status': 'error',
                    'message': 'No transaction data available'
                }

            return {
                'status': 'success',
                'data': {
                    'bank_id': result[0],
                    'bank_name': result[1],
                    'active_users_count': result[2]
                }
            }

        except Exception as e:
            logger.error(f"Failed to get active users: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'message': 'Failed to calculate active users'
            }

    @db_connection
    def cleanup_incomplete_data(self, cursor=None) -> Dict:
        """Delete users and accounts with missing required information."""
        cursor.execute('''
            DELETE FROM Account 
            WHERE user_id IN (
                SELECT id FROM User 
                WHERE name IS NULL OR surname IS NULL OR birth_day IS NULL
            )
        ''')
        cursor.execute('''
            DELETE FROM User 
            WHERE name IS NULL OR surname IS NULL OR birth_day IS NULL
        ''')
        return {
            'status': 'success',
            'message': 'Cleaned up incomplete data'
        }

    @db_connection
    def get_user_transactions(self, user_id: int, months: int = 3, cursor=None) -> List[Dict]:
        """Get transactions for a user in the last N months."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30 * months)

        cursor.execute('''
            SELECT * FROM "Transaction"
            WHERE account_sender_id IN (
                SELECT id FROM Account WHERE user_id = ?
            )
            AND datetime BETWEEN ? AND ?
            ORDER BY datetime DESC
        ''', (user_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))

        return [dict(row) for row in cursor.fetchall()]