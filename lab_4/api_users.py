import logging
import csv
from ananko_pythonCource.lab_6.validation import validate_user_full_name, ValidationError
from db_utils import db_connection

@db_connection
def add_users(cur, *users):
    if len(users) == 1 and isinstance(users[0], list):
        users = users[0]

    added = 0
    for user in users:
        user_full_name = user.get("user_full_name")
        if not user_full_name:
            logging.warning("User without user_full_name skipped")
            continue
        try:
            name, surname = validate_user_full_name(user_full_name)
            accounts = user.get("Accounts")
            if not accounts:
                logging.warning(f"User '{user_full_name}' has empty Accounts field. Skipped.")
                continue
            birth_day = user.get("Birth_day")
            cur.execute("""
                INSERT INTO User (Name, Surname, Birth_day, Accounts) VALUES (?, ?, ?, ?)
            """, (name, surname, birth_day, accounts))
            added += 1
        except ValidationError as e:
            logging.warning(f"Validation error for user '{user_full_name}': {e}")
        except Exception as e:
            logging.warning(f"Error adding user '{user_full_name}': {e}")
    return f"{added} users added successfully."

@db_connection
def add_users_csv(cur, csv_path):
    added = 0
    try:
        with open(csv_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                user_full_name = row.get("user_full_name")
                accounts = row.get("Accounts")
                birth_day = row.get("Birth_day")
                if not user_full_name or not accounts:
                    continue
                try:
                    name, surname = validate_user_full_name(user_full_name)
                    cur.execute("""
                        INSERT INTO User (Name, Surname, Birth_day, Accounts)
                        VALUES (?, ?, ?, ?)
                    """, (name, surname, birth_day, accounts))
                    added += 1
                except ValidationError as e:
                    logging.warning(f"Validation error for user '{user_full_name}': {e}")
                except Exception as e:
                    logging.warning(f"Error adding user '{user_full_name}': {e}")
    except Exception as e:
        logging.error(f"Failed to read users csv: {e}")
        raise
    return f"{added} users added from CSV."

@db_connection
def modify_user(cur, user_id, update_fields: dict):
    set_clauses = []
    params = []
    if "user_full_name" in update_fields:
        try:
            name, surname = validate_user_full_name(update_fields["user_full_name"])
        except ValidationError as e:
            return f"Validation error: {e}"
        set_clauses.extend(["Name = ?", "Surname = ?"])
        params.extend([name, surname])
    if "Birth_day" in update_fields:
        set_clauses.append("Birth_day = ?")
        params.append(update_fields["Birth_day"])
    if "Accounts" in update_fields:
        set_clauses.append("Accounts = ?")
        params.append(update_fields["Accounts"])
    if not set_clauses:
        return "Nothing to update."
    params.append(user_id)
    sql = f"UPDATE User SET {', '.join(set_clauses)} WHERE id = ?"
    try:
        cur.execute(sql, params)
        if cur.rowcount == 0:
            return f"No user with id={user_id} found."
        return f"User id={user_id} updated successfully."
    except Exception as e:
        return f"Error: {e}"

@db_connection
def delete_user(cur, user_id):
    cur.execute("DELETE FROM Account WHERE User_id = ?", (user_id,))
    cur.execute("DELETE FROM User WHERE id = ?", (user_id,))
    if cur.rowcount == 0:
        return f"No user with id={user_id} found."
    return f"User id={user_id} and their accounts deleted."
