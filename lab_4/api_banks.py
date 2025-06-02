import csv
import logging
import sqlite3
from db_utils import db_connection

@db_connection
def add_banks(cur, *banks):
    if len(banks) == 1 and isinstance(banks[0], list):
        banks = banks[0]
    added = 0
    for bank in banks:
        name = bank.get("name")
        if not name:
            logging.warning("Bank without name skipped")
            continue
        try:
            cur.execute("INSERT INTO Bank (name) VALUES (?)", (name,))
            added += 1
        except sqlite3.IntegrityError:
            logging.warning(f"Bank name '{name}' already exists. Skipped.")
    return f"{added} banks added successfully."

@db_connection
def add_banks_csv(cur, csv_path):
    added = 0
    try:
        with open(csv_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                name = row.get("name")
                if not name:
                    continue
                try:
                    cur.execute("INSERT INTO Bank (name) VALUES (?)", (name,))
                    added += 1
                except sqlite3.IntegrityError:
                    logging.warning(f"Bank '{name}' already exists. Skipped.")
    except Exception as e:
        logging.error(f"Failed to read banks csv: {e}")
        raise
    return f"{added} banks added from CSV."

@db_connection
def modify_bank(cur, bank_id, update_fields: dict):
    if not update_fields:
        return "Nothing to update."
    set_clauses = []
    params = []
    if "name" in update_fields:
        set_clauses.append("name = ?")
        params.append(update_fields["name"])
    params.append(bank_id)
    sql = f"UPDATE Bank SET {', '.join(set_clauses)} WHERE id = ?"
    try:
        cur.execute(sql, params)
        if cur.rowcount == 0:
            return f"No bank with id={bank_id} found."
        return f"Bank id={bank_id} updated successfully."
    except Exception as e:
        return f"Error: {e}"

@db_connection
def delete_bank(cur, bank_id):
    cur.execute("DELETE FROM Account WHERE Bank_id = ?", (bank_id,))
    cur.execute("DELETE FROM Bank WHERE id = ?", (bank_id,))
    if cur.rowcount == 0:
        return f"No bank with id={bank_id} found."
    return f"Bank id={bank_id} and related accounts deleted."
