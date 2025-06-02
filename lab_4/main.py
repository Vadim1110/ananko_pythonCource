from api_banks import add_banks, add_banks_csv
from api_users import add_users, add_users_csv
from api_accounts import add_accounts
from api_transactions import transfer_money

def main():
    print(add_banks({"name": "monobank"}))
    print(add_banks_csv("banks.csv"))

    print(add_users({"user_full_name": "Ivan Ivanov", "Birth_day": "1990-01-01", "Accounts": "12345"}))
    print(add_users_csv("users.csv"))

    print(add_accounts({
        "User_id": 1,
        "Type": "debit",
        "Account_Number": "AB12345678",
        "Bank_id": 1,
        "Currency": "UA",
        "Amount": 10000,
        "Status": "gold"
    }))

    print(transfer_money(1, 2, 100))

if __name__ == "__main__":
    main()
