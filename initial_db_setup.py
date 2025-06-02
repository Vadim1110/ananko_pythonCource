import sqlite3
import argparse
import os


def create_database(unique_name_surname: bool = False, db_path: str = 'bank_system.db') -> None:
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE Bank (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
    ''')

    user_table_sql = '''
    CREATE TABLE User (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        surname TEXT NOT NULL,
        birth_day TEXT,
        Accounts TEXT NOT NULL
    '''
    if unique_name_surname:
        user_table_sql += ', UNIQUE (name, surname)'
    user_table_sql += ')'
    cursor.execute(user_table_sql)

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

    conn.commit()
    conn.close()
    print(f"Database created successfully at {db_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Initialize the bank system database.')
    parser.add_argument('--unique-name-surname', action='store_true',
                        help='Enforce uniqueness on User name and surname combination')
    parser.add_argument('--db-path', type=str, default='bank_system.db',
                        help='Path to the database file')
    args = parser.parse_args()

    create_database(args.unique_name_surname, args.db_path)
