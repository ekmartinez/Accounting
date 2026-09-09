import pandas as pd

class Ledger:
    """A simple helper to record and display journal entries for accounting problems."""

    def __init__(self):
        self.entries = []
        self._next_id = 1

    def add_entry(self, lines, description=None):
        """
        Add a journal entry made up of one or more lines.
        'lines' is a list of dicts, each like:
            {"date": ..., "account": ..., "debit": 0, "credit": 0}
        'description' is an optional string explaining the transaction.
        The entry must balance (within rounding tolerance) or it's rejected.
        Prints and returns the auto-assigned transaction id.
        """
        required_keys = {"date", "account", "debit", "credit"}
        for line in lines:
            if not required_keys.issubset(line):
                missing = required_keys - line.keys()
                raise ValueError(f"Line is missing required keys: {missing}")

        total_debit = round(sum(line["debit"] for line in lines), 2)
        total_credit = round(sum(line["credit"] for line in lines), 2)

        if total_debit != total_credit:
            raise ValueError(
                f"Entry does not balance: debits={total_debit}, credits={total_credit}"
            )

        txn_id = self._next_id
        for line in lines:
            line["txn_id"] = txn_id
            line["description"] = description

        self.entries.extend(lines)
        self._next_id += 1

        desc_note = f" — {description}" if description else ""
        print(f"Saved transaction id {txn_id}{desc_note}")

        return txn_id

    def delete_transaction(self, txn_id):
        """Remove all lines belonging to a given transaction id."""
        before = len(self.entries)
        self.entries = [e for e in self.entries if e["txn_id"] != txn_id]
        removed = before - len(self.entries)

        if removed == 0:
            print(f"No transaction found with id {txn_id}.")
        else:
            print(f"Deleted transaction id {txn_id} ({removed} line(s) removed).")
            
    def print_transaction(self, txn_id=None):
        """
        Print journal entries.
        If txn_id is given, prints only that transaction.
        If txn_id is omitted, prints the entire ledger, grouped by transaction,
        with each transaction's description printed once at the end of its lines.
        """
        if not self.entries:
            print("No entries recorded yet.")
            return

        if txn_id is None:
            lines = self.entries
            show_id_column = True
        else:
            lines = [e for e in self.entries if e["txn_id"] == txn_id]
            if not lines:
                print(f"No transaction found with id {txn_id}.")
                return
            show_id_column = False

        if show_id_column:
            print(f"{'ID':<5}{'Date':<12}{'Account':<25}{'Debit':>10}{'Credit':>10}")
            print("-" * 62)
        else:
            print(f"{'Date':<12}{'Account':<25}{'Debit':>10}{'Credit':>10}")
            print("-" * 57)

        # Group lines by txn_id while preserving order of first appearance
        grouped = {}
        for e in lines:
            grouped.setdefault(e["txn_id"], []).append(e)

        for group in grouped.values():
            for e in group:
                debit = e["debit"] if e["debit"] else ""
                credit = e["credit"] if e["credit"] else ""

                if show_id_column:
                    print(f"{e['txn_id']:<5}{str(e['date']):<12}{e['account']:<25}{str(debit):>10}{str(credit):>10}")
                else:
                    print(f"{str(e['date']):<12}{e['account']:<25}{str(debit):>10}{str(credit):>10}")

            description = group[0]["description"]
            if description:
                indent = "      " if show_id_column else "    "
                print(f"{indent}({description})")

    def to_table(self):
        """
        Return the ledger as a pandas DataFrame, with columns:
        txn_id, date, account, debit, credit, description.
        Requires pandas to be installed.
        """

        if not self.entries:
            return pd.DataFrame(columns=["txn_id", "date", "account", "debit", "credit", "description"])

        return pd.DataFrame(self.entries)[
            ["txn_id", "date", "account", "debit", "credit", "description"]
        ]

    def reset(self):
        """Clear all entries and restart the transaction id counter from 1."""
        self.entries = []
        self._next_id = 1
        print("Ledger has been reset.") 

class TrialBalance:
    """
    Stores account balances for a trial balance. Can be built manually or
    imported from a spreadsheet. Corrections are applied by posting entries
    to a Ledger and then calling apply_ledger() — balances are never edited
    directly.
    """

    def __init__(self):
        # account name -> {"debit": float, "credit": float, "type": str or None}
        self.accounts = {}

    def add_account(self, account, debit=0, credit=0, account_type=None):
        """Add a new account (or overwrite an existing one) with a starting balance."""
        self.accounts[account] = {
            "debit": debit,
            "credit": credit,
            "type": account_type,
        }

    def remove_account(self, account):
        """Remove an account entirely (e.g., it shouldn't have existed)."""
        self.accounts.pop(account, None)

    def adjust_account(self, account, debit_change=0, credit_change=0):
        """
        Apply an incremental correction to an existing account's balance.
        Use for clerical errors (e.g., a footing understated by $100) —
        NOT for correcting a real transaction, which should go through
        apply_ledger() instead as a proper journal entry.
        """
        if account not in self.accounts:
            raise KeyError(f"Account '{account}' not found. Use add_account() first.")
        self.accounts[account]["debit"] += debit_change
        self.accounts[account]["credit"] += credit_change

    def set_account(self, account, debit=0, credit=0):
        """
        Overwrite an account's balance directly.
        Use when you're told the correct final balance outright
        (e.g., a transposition error's corrected amount).
        """
        if account not in self.accounts:
            raise KeyError(f"Account '{account}' not found. Use add_account() first.")
        self.accounts[account]["debit"] = debit
        self.accounts[account]["credit"] = credit


    def apply_ledger(self, ledger, account_types=None):
        """
        Add the debit/credit amounts from every line in a Ledger into this
        trial balance's account totals. Accounts not already on the trial
        balance are added automatically. 'account_types' is an optional dict
        for labeling any newly-added accounts (e.g., {"Dividends": "equity"}).
        """
        account_types = account_types or {}
        for entry in ledger.entries:
            account = entry["account"]
            if account not in self.accounts:
                self.add_account(account, account_type=account_types.get(account))
            self.accounts[account]["debit"] += entry["debit"]
            self.accounts[account]["credit"] += entry["credit"]

    def totals(self):
        """Return (total_debit, total_credit)."""
        total_debit = sum(a["debit"] for a in self.accounts.values())
        total_credit = sum(a["credit"] for a in self.accounts.values())
        return round(total_debit, 2), round(total_credit, 2)

    def is_balanced(self):
        """True if total debits equal total credits."""
        total_debit, total_credit = self.totals()
        return total_debit == total_credit

    def reset(self):
        """Clear all accounts from the trial balance."""
        self.accounts = {}
        print("Trial balance has been reset.")

    def to_table(self, include_total=True, include_difference=False, net=True):
        """
        Return the trial balance as a pandas DataFrame.
        By default, shows each account's balance netted to one side (the
        standard "final" trial balance view) — needed once corrections have
        posted to both sides of an account.
        Pass net=False to see raw debit/credit totals as stored separately
        instead — useful mid-problem while auditing footing errors.
        """
        rows = []
        for name, data in self.accounts.items():
            debit, credit = data["debit"], data["credit"]
            if net:
                balance = round(debit - credit, 2)
                debit, credit = (balance, 0) if balance >= 0 else (0, -balance)
            rows.append({"account": name, "debit": debit, "credit": credit, "type": data["type"]})

        df = pd.DataFrame(rows, columns=["account", "debit", "credit", "type"])

        total_debit = round(df["debit"].sum(), 2) if not df.empty else 0
        total_credit = round(df["credit"].sum(), 2) if not df.empty else 0

        if include_total:
            totals_row = pd.DataFrame([{
                "account": "TOTAL", "debit": total_debit, "credit": total_credit, "type": "",
            }])
            df = pd.concat([df, totals_row], ignore_index=True)

        if include_difference:
            difference = round(total_debit - total_credit, 2)
            diff_row = pd.DataFrame([{
                "account": "DIFFERENCE", "debit": difference if difference > 0 else 0,
                "credit": -difference if difference < 0 else 0, "type": "",
            }])
            df = pd.concat([df, diff_row], ignore_index=True)

        return df
    
    @classmethod
    def from_dataframe(cls, df, account_col="account",
                        debit_col=None, credit_col=None, amount_col=None,
                        type_col=None):
        """
        Build a TrialBalance from a DataFrame (e.g., pd.read_excel / pd.read_csv).
        Pass either amount_col (single signed column) OR debit_col/credit_col
        (two-column layout) — not both.
        """
        if amount_col is not None and (debit_col or credit_col):
            raise ValueError("Provide either amount_col, or debit_col/credit_col — not both.")

        tb = cls()
        for _, row in df.iterrows():
            account = row[account_col]
            acct_type = row[type_col] if type_col else None

            if amount_col is not None:
                amount = row[amount_col]
                debit = amount if amount > 0 else 0
                credit = -amount if amount < 0 else 0
            else:
                debit = row[debit_col] if debit_col else 0
                credit = row[credit_col] if credit_col else 0
                debit = 0 if pd.isna(debit) else debit
                credit = 0 if pd.isna(credit) else credit

            tb.add_account(account, debit=debit, credit=credit, account_type=acct_type)

        return tb

"""
Usage:

    # Create a new ledger (do this once per exercise)
    ledger = Ledger()

    # Add a journal entry — pass a list of line dicts (2 or more lines).
    # Each line needs: date, account, debit, credit.
    # 'description' is optional and applies to the whole entry.
    # The entry is rejected if debits don't equal credits.
    # Returns the auto-assigned transaction id, and prints it too.
    txn_id = ledger.add_entry(
        [
            {"date": "2024-05-01", "account": "Cash", "debit": 4000, "credit": 0},
            {"date": "2024-05-01", "account": "Common Stock", "debit": 0, "credit": 4000},
        ],
        description="Issued common stock for cash",
    )

    # Print the full ledger (all transactions, grouped, with an ID column)
    ledger.print_transaction()

    # Print just one transaction by its id (no ID column, since it's implied)
    ledger.print_transaction(txn_id)

    # Delete a transaction by id (e.g., to fix a duplicate or mistake)
    ledger.delete_transaction(txn_id)

    # Reset the ledger back to empty and restart ids from 1
    # (use sparingly — usually prefer creating a new Ledger() per exercise instead)
    ledger.reset()
"""

"""
Trial balance usage:

    # Create an empty trial balance
    tb = TrialBalance()

    # Add accounts manually, with their stated (possibly incorrect) balances
    tb.add_account("Cash", debit=4800, account_type="asset")
    tb.add_account("Accounts Payable", credit=4500, account_type="liability")
    # 'account_type' is optional — useful later for financial statements,
    # but not required just to build/balance a trial balance.

    # OR build it from a spreadsheet instead of typing it by hand.
    # Works with either a single signed amount column...
    df = pd.read_excel("trial_balance.xlsx")
    tb = TrialBalance.from_dataframe(df, account_col="Account", amount_col="Amount")

    # ...or a two-column debit/credit layout.
    tb = TrialBalance.from_dataframe(
        df, account_col="Account", debit_col="Debit", credit_col="Credit"
    )

    # Corrections are NOT made by editing tb directly. Post them as real
    # journal entries in a Ledger, exactly like any other transaction.
    corrections = Ledger()
    corrections.add_entry(
        [
            {"date": "2025-06-30", "account": "Cash", "debit": 180, "credit": 0},
            {"date": "2025-06-30", "account": "Accounts Receivable", "debit": 0, "credit": 180},
        ],
        description="Correct understated cash collection",
    )
    # Repeat add_entry() for each correction needed.

    # Once all corrections are posted, fold the ledger into the trial balance.
    # Any account mentioned in the ledger that isn't already on tb gets added
    # automatically (optionally labeled via account_types).
    tb.apply_ledger(corrections, account_types={"Dividends": "equity"})

    # Check the result
    tb.is_balanced()     # True/False
    tb.totals()          # (total_debit, total_credit)
    tb.to_table()        # pandas DataFrame, with a TOTAL row by default
    tb.to_table(include_total=False)   # without the TOTAL row

    # Remove an account entirely, if it shouldn't be on the trial balance at all
    tb.remove_account("Some Wrong Account")
"""
