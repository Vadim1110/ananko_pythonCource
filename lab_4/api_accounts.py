import logging
import csv
from ananko_pythonCource.lab_6.validation import (
    validate_strict_field,
    validate_account_number,
    ValidationError
)
from db_utils import db_connection

@db_connection
def add_accounts(cur, *accounts):
    if len(accounts) == 1 and isinstance(accounts[0], list):
        accounts = accounts[0]
    added = 0
    for acc in accounts:
        try:
            user_id = acc["User_id"]
            acc_type = acc["Type"]
            account_number = acc["Account_Number"]
            bank_id = acc["Bank_id"]
            currency = acc["Currency"]
            amount = acc["Amount"]
            status = acc.get("Status")

            validate_strict_field(acc_type, "Type", ['credit', 'debit'])
            validate_strict_field(status, "Status", ['gold', 'silver', 'platinum'])
            account_number = validate_account_number(account_number)

            cur.execute("""
                INSERT INTO Account
                (User_id, Type, Account_Number, Bank_id, Currency, Amount, Status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, acc_type, account_number, bank_id, currency, amount, status))
            added += 1
        except KeyError as e:
            logging.warning(f"Missing field {e} in account. Skipped.")
        except ValidationError as e:
            logging.warning(f"Validation error for account {acc.get('Account_Number')}: {e}")
        except Exception as e:
            logging.warning(f"Error adding account {acc.get('Account_Number')}: {e}")
    return f"{added} accounts added successfully."

@db_connection
def add_accounts_csv(cur, csv_path):
    added = 0
    try:
        with open(csv_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    user_id = int(row["User_id"])
                    acc_type = row["Type"]
                    account_number = row["Account_Number"]
                    bank_id = int(row["Bank_id"])
                    currency = row["Currency"]
                    amount = float(row["Amount"])
                    status = row.get("Status")
                    validate_strict_field(acc_type, "Type", ['credit', 'debit'])
                    validate_strict_field(status, "Status", ['gold', 'silver', 'platinum'])
                    account_number = validate_account_number(account_number)

                    cur.execute("""
                        INSERT INTO Account
                        (User_id, Type, Account_Number, Bank_id, Currency, Amount, Status)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (user_id, acc_type, account_number, bank_id, currency, amount, status))
                    added += 1
                except Exception as e:
                    logging.warning(f"Error in account CSV row: {e}")
    except Exception as e:
        logging.error(f"Failed to read accounts csv: {e}")
        raise
    return f"{added} accounts added from CSV."

@db_connection
def modify_account(cur, account_id, update_fields: dict):
    if not update_fields:
        return "Nothing to update."
    set_clauses = []
    params = []
    if "Type" in update_fields:
        try:
            validate_strict_field(update_fields["Type"], "Type", ['credit', 'debit'])
        except ValidationError as e:
            return f"Validation error: {e}"
        set_clauses.append("Type = ?")
        params.append(update_fields["Type"])
    if "Account_Number" in update_fields:
        try:
            acc_num = validate_account_number(update_fields["Account_Number"])
        except ValidationError as e:
            return f"Validation error: {e}"
        set_clauses.append("Account_Number = ?")
        params.append(acc_num)
    if "Bank_id" in update_fields:
        set_clauses.append("Bank_id = ?")
        params.append(update_fields["Bank_id"])
    if "User_id" in update_fields:
        set_clauses.append("User_id = ?")
        params.append(update_fields["User_id"])
    if "Currency" in update_fields:
        set_clauses.append("Currency = ?")
        params.append(update_fields["Currency"])
    if "Amount" in update_fields:
        set_clauses.append("Amount = ?")
        params.append(update_fields["Amount"])
    if "Status" in update_fields:
        try:
            validate_strict_field(update_fields["Status"], "Status", ['gold', 'silver', 'platinum'])
        except ValidationError as e:
            return f"Validation error: {e}"
        set_clauses.append("Status = ?")
        params.append(update_fields["Status"])

    params.append(account_id)
    sql = f"UPDATE Account SET {', '.join(set_clauses)} WHERE id = ?"
    try:
        cur.execute(sql, params)
        if cur.rowcount == 0:
            return f"No account with id={account_id} found."
        return f"Account id={account_id} updated successfully."
    except Exception as e:
        return f"Error: {e}"

@db_connection
def delete_account(cur, account_id):
    cur.execute("DELETE FROM Account WHERE id = ?", (account_id,))
    if cur.rowcount == 0:
        return f"No account with id={account_id} found."
    return f"Account id={account_id} deleted."
