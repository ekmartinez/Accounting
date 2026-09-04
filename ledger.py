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
    def print_transaction(self, txn_id=None):
        """
        Print journal entries.
        If txn_id is given, prints only that transaction.
        If txn_id is omitted, prints the entire ledger.
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

        last_description = None
        for e in lines:
            debit = e["debit"] if e["debit"] else ""
            credit = e["credit"] if e["credit"] else ""

            if show_id_column:
                print(f"{e['txn_id']:<5}{str(e['date']):<12}{e['account']:<25}{str(debit):>10}{str(credit):>10}")
            else:
                print(f"{str(e['date']):<12}{e['account']:<25}{str(debit):>10}{str(credit):>10}")

            if e["description"] and e["description"] != last_description:
                indent = "      " if show_id_column else "    "
                print(f"{indent}({e['description']})")
            last_description = e["description"]    
    
"""
Usage:

ledger = Ledger()

id1 = ledger.add_entry(
    [
        {"date": "2024-01-01", "account": "Cash", "debit": 5000, "credit": 0},
        {"date": "2024-01-01", "account": "Common Stock", "debit": 0, "credit": 5000},
    ],
    description="Issued common stock for cash",
)

ledger.add_entry(
    [
        {"date": "2024-01-05", "account": "Equipment", "debit": 8000, "credit": 0},
        {"date": "2024-01-05", "account": "Cash", "debit": 0, "credit": 2000},
        {"date": "2024-01-05", "account": "Notes Payable", "debit": 0, "credit": 6000},
    ],
    description="Purchased equipment, partial cash and note",
)

ledger.print_transaction()      # prints the whole ledger, with ID column
ledger.print_transaction(3)     # prints just transaction 3, no ID column (redundant when there's only one)

"""
