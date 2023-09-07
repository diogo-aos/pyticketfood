import datetime as dt
from dataclasses import dataclass
from typing import List, Tuple
from pathlib import Path
import pickle
import warnings

from ticket import get_transactions, Transaction



@dataclass
class TransactionDatabase:
    """Class for keeping track of an item in inventory."""
    transactions: List[Transaction]
    last_update: dt.datetime
    balance: float

class Ticket:
    def __init__(self, creds: Tuple[str, str], path: Path = None):
        self.username = creds[0]
        self.password = creds[1]

        
        # load from local file, if provided
        if path is not None and path.exists() and path.is_file():
            with self.path.open("rb") as f:
                self.db = pickle.load(f)
        else:
            self.init_db()

        self.path = path

    
    def update(self, update_period: dt.timedelta = dt.timedelta(minutes=60)) -> Tuple[float, List[Transaction]]:
        balance, ret_transactions = None, []
        if self.db is not None:
            if dt.datetime.now() >= (self.db.last_update + update_period):
                balance, ret_transactions = self.get_new_transactions()
            else:
                warnings.warn(f"update period ({update_period}) has not yet elapsed since last update ({self.db.last_update})")
        else:
            balance, ret_transactions = self.init_db()

        
        # save database to pickle
        with self.path.open("wb") as f:
            pickle.dump(self.db, f)

        return balance, ret_transactions


    def init_db(self) -> Tuple[float, List[Transaction]]:
        balance, T = self.get_transactions(self.username, self.password, dt.datetime(2000, 1, 1), dt.datetime.today())
        self.db = TransactionDatabase(
            transactions=T,
            last_update=dt.datetime.now(), 
            balance=balance
        )
        return balance, self.db.transactions


    def get_new_transactions(self) -> Tuple[float, List[Transaction]]:
        # get date of last transaction
        last_date = sorted(self.db.transactions, key=lambda x: x.date)[-1].date

        # get new transactions from website, from last date to today
        balance, new_T = get_transactions(self.username, self.password, last_date, dt.datetime.today())

        # remove duplicate transactions between database and new transactions
        new_T = [t for t in new_T if t not in self.db.transactions]

        self.db.transactions += new_T
        self.balance = balance
        self.last_update = dt.datetime.now()

        return balance, new_T
    

def main():
    import os
    cred_vars = ['TICKET_USER', 'TICKET_PASS']
    credentials = []
    for v_name in cred_vars:
        if v_name not in os.environ:
            v_val = input(f'insert {v_name}:')
        else:
            v_val = os.environ[v_name]
        credentials.append(v_val)
        
    database_path = Path('database.pickle')
    ticket = Ticket(creds=credentials, path=database_path)
    balance, T = ticket.update() # get new transactions, or init database if no db exists yet
    # from now on, I can just call the update method to get **new** transactions
    print(sorted(T, key=lambda x: x.date)) # sort by date


if __name__ == '__main__':
    main()