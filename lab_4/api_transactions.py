import logging
from db_utils import db_connection

@db_connection
def transfer_money(cur, from_account_id, to_account_id, amount):
    if amount <= 0:
        return "Amount must be positive."

    cur.execute("SELECT Amount FROM Account WHERE id = ?", (from_account_id,))
    from_acc = cur.fetchone()
    if not from_acc:
        return f"From account id={from_account_id} not found."
    if from_acc[0] < amount:
        return f"Insufficient funds in account id={from_account_id}."

    cur.execute("SELECT Amount FROM Account WHERE id = ?", (to_account_id,))
    to_acc = cur.fetchone()
    if not to_acc:
        return f"To account id={to_account_id} not found."

    try:
        cur.execute("UPDATE Account SET Amount = Amount - ? WHERE id = ?", (amount, from_account_id))
        cur.execute("UPDATE Account SET Amount = Amount + ? WHERE id = ?", (amount, to_account_id))
        return f"Transferred {amount} from account {from_account_id} to {to_account_id} successfully."
    except Exception as e:
        logging.error(f"Transfer error: {e}")
        return f"Transfer failed: {e}"
