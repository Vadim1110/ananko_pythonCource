import sqlite3
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='bank_system.log'
)
logger = logging.getLogger(__name__)


class DatabaseConnection:

    def __init__(self, db_path='bank_system.db'):
        self.db_path = db_path
        self.conn = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn.cursor()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
            self.conn.close()


class BankSystem:

    def __init__(self):
        self.exchange_api_key = "fca_live_oi2Tqoxa5XaJu0C9Df2hwog7LzhBns350jYCHINH"
        self.exchange_base_url = "https://api.freecurrencyapi.com/v1/latest"
