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

    def reset(self):
        """Clear all entries and restart the transaction id counter from 1."""
        self.entries = []
        self._next_id = 1
        print("Ledger has been reset.") 

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
