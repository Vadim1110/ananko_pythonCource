from api import BankAPI
import logging
from pprint import pprint
from datetime import datetime, timedelta

def demo_transfer(api, sender_id, receiver_id, amount, currency, description):
    print(f"\n{description}")
    display_accounts(api, [sender_id, receiver_id])
    result = api.transfer_money({
        'sender_account_id': sender_id,
        'receiver_account_id': receiver_id,
        'amount': amount,
        'currency': currency
    })
    pprint(result)
    if result['status'] == 'success':
        print("Transfer successful. New balances:")

        display_accounts(api, [sender_id, receiver_id])
    else:
        print("Transfer failed. Original balances maintained:")
        display_accounts(api, [sender_id, receiver_id])

def display_accounts(api, account_ids):
    print("\nAccount Balances:")
    for acc_id in account_ids:
        account = api.get_account(acc_id)
        if account:
            print(f"Account {acc_id}: {account['amount']:.2f} {account['currency']} ({account['type']})")
        else:
            print(f"Account {acc_id}: Not found")


def initialize_sample_data(api):
    print("\n=== Initializing Sample Data ===")

    banks = [
        {'name': 'Global USD Bank'},
        {'name': 'European EUR Bank'},
        {'name': 'Asia JPY Bank'}
    ]
    api.add_banks(banks)

    users = [
        {'user_full_name': 'Alex Johnson', 'birth_day': '1985-04-12'},
        {'user_full_name': 'Maria Garcia', 'birth_day': '1990-11-05'},
        {'user_full_name': 'James Wilson', 'birth_day': '1978-07-22'}
    ]
    api.add_users(users)

    accounts = [
        {
            'user_id': 1, 'type': 'debit', 'account_number': 'ID-j3-q-4332547-u9',
            'bank_id': 1, 'currency': 'USD', 'amount': 10000.00, 'status': 'platinum'
        },
        {
            'user_id': 2, 'type': 'credit', 'account_number': 'ID-EUR-2001333334-',
            'bank_id': 2, 'currency': 'EUR', 'amount': -1000.00, 'status': 'silver'
        },
        {
            'user_id': 3, 'type': 'credit', 'account_number': 'ID-JPY-3001555553-',
            'bank_id': 3, 'currency': 'JPY', 'amount': 1200000.00, 'status': 'silver'
        },
        {
            'user_id': 1, 'type': 'credit', 'account_number': 'ID-USD-1002000003-',
            'bank_id': 1, 'currency': 'USD', 'amount': 5000.00, 'status': 'gold'
        }
    ]
    result = api.add_accounts(accounts)
    return [acc['id'] for acc in result['data']] if result['status'] == 'success' else []


def demo_international_payments(api, account_ids):
    print("\nInternational payments")

    print("\n1. Business Payment (USD -> EUR)")
    print("Alex 500 US -> Maria")
    demo_transfer(api, account_ids[0], account_ids[1], 500, 'USD', "Example")

    print("\n2. Travel Payment (EUR -> JPY)")
    print("Maria 300 EUR -> James ")
    demo_transfer(api, account_ids[1], account_ids[2], 300, 'EUR', "Example")

def demo_personal_finance(api, account_ids):
    print("\nPersonal payments")

    print("\n1. Savings Transfer")
    print("Alex -> $1000 to another acc")
    demo_transfer(api, account_ids[0], account_ids[3], 1000, 'USD', "Example")


def demo_banking_features(api, account_ids):
    print("\n=== Banking Features ===")
    print("\nAccount Details:")
    for i, acc_id in enumerate(account_ids, 1):
        account = api.get_account(acc_id)
        print(f"{i}.{account['id']} - {account['user_id']} - {account['bank_name']} - {account['amount']:.2f} {account['currency']} - {account['status']}")


def demo_advanced_features(api, account_ids):
    print("\n1. Applying random discounts to credit accounts:")
    discount_result = api.apply_random_discounts()
    if discount_result['status'] == 'success':
        print(f"Successfully applied discounts to {len(discount_result['data'])} accounts")
        for item in discount_result['data']:
            print(f"User {item['user_id']}: {item['discount']}")
    else:
        print(f"Failed to apply discounts: {discount_result['message']}")

    api.transfer_money({
        'sender_account_id': account_ids[0],
        'receiver_account_id': account_ids[1],
        'amount': 15000,
        'currency': 'USD'
    })
    print("\n2. Users with debts:")
    pprint(api.get_users_with_debts())

    print("\n3. Bank with largest capital:")
    pprint(api.get_bank_with_largest_capital())

    print("\n4. Bank serving oldest client:")
    pprint(api.get_bank_with_oldest_client())

    print("\n5. Bank with most active users:")
    active_users_result = api.get_bank_with_most_active_users()
    if active_users_result['status'] == 'success':
        data = active_users_result['data']
        print(f"Bank: {data['bank_name']} (ID: {data['bank_id']})")
        print(f"Unique active users: {data['active_users_count']}")
    else:
        print(f"Error: {active_users_result['message']}")

    print("\n6. Transaction History for Account 1:")
    transactions = api.get_transactions(
        account_id=account_ids[0],
        start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
        end_date=datetime.now().strftime('%Y-%m-%d')
    )
    pprint(transactions)

    print("\n7. Data cleanup (simulated):")
    pprint(api.cleanup_incomplete_data())

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    try:
        api = BankAPI()

        account_ids = initialize_sample_data(api)
        if not account_ids:
            print("Failed to initialize accounts")
            return

        display_accounts(api, account_ids)

        demo_international_payments(api, account_ids)
        demo_personal_finance(api, account_ids)
        demo_banking_features(api, account_ids)

        demo_advanced_features(api, account_ids)

    except Exception as e:
        logging.error(f"Application error: {str(e)}")

if __name__ == "__main__":
    main()